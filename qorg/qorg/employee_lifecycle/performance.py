from __future__ import annotations

import json
from decimal import Decimal

import frappe
from frappe import _
from frappe.utils import add_days, flt, getdate, now_datetime, today

SOURCES = {"Goals", "Self", "Direct Manager", "Peers", "Human Resources", "Senior Management", "Related Department", "Direct Reports", "Technical Assessor", "Other"}
FINAL_ASSIGNMENT_STATES = {"Submitted", "Declined", "Replaced", "Cancelled"}


def validate_rating_scale(doc):
    if not doc.bands:
        frappe.throw(_("At least one Rating Band is required."))
    ranges = []
    for row in doc.bands:
        low, high = flt(row.min_score), flt(row.max_score)
        if not (0 <= low <= high <= 100):
            frappe.throw(_("Rating band scores must be between 0 and 100, with Minimum not greater than Maximum."))
        ranges.append((Decimal(str(low)), Decimal(str(high)), row.idx))
        if row.outcome == "Development Plan":
            row.development_required = 1
    ranges.sort()
    if ranges[0][0] != Decimal("0") or ranges[-1][1] != Decimal("100"):
        frappe.throw(_("Rating bands must cover the full 0 to 100 range."))
    previous_high = None
    for low, high, idx in ranges:
        if previous_high is not None and low > previous_high + Decimal("0.01"):
            frappe.throw(_("Rating Scale has a gap before row {0}.").format(idx))
        if previous_high is not None and low <= previous_high:
            frappe.throw(_("Rating Scale bands overlap at row {0}.").format(idx))
        previous_high = high


def validate_evaluation_type(doc):
    if not doc.sources:
        frappe.throw(_("At least one Evaluation Source is required."))
    if flt(doc.source_score_max) <= 0:
        frappe.throw(_("Source Score Maximum must be greater than zero."))
    seen, included_weight = set(), Decimal("0")
    for row in doc.sources:
        if row.source not in SOURCES:
            frappe.throw(_("Unsupported Evaluation Source: {0}.").format(row.source))
        if row.source in seen:
            frappe.throw(_("Duplicate Evaluation Source: {0}.").format(row.source))
        seen.add(row.source)
        if row.required_reviewers < 1 or row.min_reviews < 1:
            frappe.throw(_("Reviewer counts must be at least one."))
        if row.min_reviews > row.required_reviewers:
            frappe.throw(_("Minimum Completed Reviews cannot exceed Required Reviewers for {0}.").format(row.source))
        if row.source in {"Goals", "Self"}:
            row.assignment_required = 0
        if row.source == "Self" and row.required_reviewers != 1:
            frappe.throw(_("Self evaluation requires exactly one reviewer."))
        if row.source == "Direct Manager" and row.assignment_strategy not in {"Direct Supervisor", "Manual"}:
            frappe.throw(_("Direct Manager must use Direct Supervisor or Manual assignment."))
        if row.include_score:
            included_weight += Decimal(str(flt(row.weight)))
    if included_weight != Decimal("100"):
        frappe.throw(_("Included Evaluation Source weights must total 100%; current total is {0}.").format(included_weight))
    if doc.self_required and "Self" not in seen:
        frappe.throw(_("Self-Appraisal Required needs a Self evaluation source."))
    if not frappe.db.exists("Rating Scale", doc.rating_scale):
        frappe.throw(_("Rating Scale does not exist."))


def validate_assignment(doc):
    previous = doc.get_doc_before_save()
    appraisal = frappe.get_doc("Appraisal", doc.appraisal)
    if appraisal.employee != doc.employee:
        frappe.throw(_("Assignment Employee must match the Appraisal employee."))
    if appraisal.appraisal_cycle != doc.appraisal_cycle:
        frappe.throw(_("Assignment Appraisal Cycle must match the Appraisal."))
    if not frappe.db.exists("Evaluation Type", doc.evaluation_type):
        frappe.throw(_("Evaluation Type does not exist."))
    policy = frappe.get_cached_doc("Evaluation Type", doc.evaluation_type)
    source = next((row for row in policy.sources if row.source == doc.evaluation_source), None)
    if not source:
        frappe.throw(_("Evaluation Source is not part of the selected Evaluation Type."))
    if doc.reviewer == doc.employee and doc.evaluation_source != "Self":
        frappe.throw(_("Employee cannot review themselves except for the Self source."))
    reviewer = frappe.get_doc("Employee", doc.reviewer)
    subject = frappe.get_doc("Employee", doc.employee)
    if source.assignment_strategy == "Direct Supervisor" and subject.reports_to != doc.reviewer:
        frappe.throw(_("Reviewer must be the employee's current direct supervisor."))
    if source.assignment_strategy == "Direct Reports" and reviewer.reports_to != doc.employee:
        frappe.throw(_("Reviewer must be a current direct report of the employee."))
    if doc.evaluation_source == "Related Department" and doc.related_department and reviewer.department != doc.related_department:
        frappe.throw(_("Reviewer must belong to the selected Related Department."))
    if reviewer.status != "Active":
        frappe.throw(_("Reviewer must be an active Employee."))
    if not reviewer.user_id:
        frappe.throw(_("Reviewer must have a linked User."))
    doc.reviewer_user = reviewer.user_id
    doc.reviewer_category = doc.evaluation_source
    doc.weight = source.weight
    doc.anonymous = 1 if source.anonymous or policy.confidentiality in {"Anonymous Sources", "Aggregated Sources Only"} else 0
    if doc.due_date and getdate(doc.due_date) < getdate(doc.assigned_on):
        frappe.throw(_("Due Date cannot be before Assigned On."))
    duplicate = frappe.db.get_value("Evaluation Assignment", {"appraisal": doc.appraisal, "evaluation_source": doc.evaluation_source, "reviewer": doc.reviewer, "status": ["not in", ["Replaced", "Cancelled"]], "name": ["!=", doc.name or ""]}, "name")
    if duplicate:
        frappe.throw(_("Active assignment already exists: {0}.").format(duplicate))
    if previous:
        if previous.status != doc.status and not doc.flags.get("evaluation_status_transition"):
            frappe.throw(_("Use assignment actions to change Status."))
        if previous.locked or previous.status in FINAL_ASSIGNMENT_STATES:
            protected = ("appraisal_cycle", "appraisal", "evaluation_type", "employee", "evaluation_source", "reviewer", "weight", "anonymous", "due_date")
            if any(doc.get(field) != previous.get(field) for field in protected):
                frappe.throw(_("Locked or final assignment values cannot be changed."))


def generate_assignments(appraisal, manual_reviewers=None):
    appraisal_doc = frappe.get_doc("Appraisal", appraisal)
    appraisal_doc.check_permission("write")
    evaluation_type = appraisal_doc.get("qorg_evaluation_type") or frappe.db.get_value("Appraisal Cycle", appraisal_doc.appraisal_cycle, "qorg_evaluation_type")
    if not evaluation_type:
        frappe.throw(_("Evaluation Type is required on the Appraisal Cycle or Appraisal."))
    policy = frappe.get_doc("Evaluation Type", evaluation_type)
    manual_reviewers = manual_reviewers or {}
    created, existing, unresolved = [], [], []
    for source in policy.sources:
        if not source.assignment_required:
            continue
        reviewers = _resolve_reviewers(appraisal_doc, source, manual_reviewers.get(source.source, []))
        if len(reviewers) < source.required_reviewers:
            unresolved.append({"source": source.source, "required": source.required_reviewers, "resolved": len(reviewers)})
        for reviewer in reviewers[: source.required_reviewers]:
            current = frappe.db.get_value("Evaluation Assignment", {"appraisal": appraisal_doc.name, "evaluation_source": source.source, "reviewer": reviewer, "status": ["not in", ["Replaced", "Cancelled"]]}, "name")
            if current:
                existing.append(current)
                continue
            assignment = frappe.get_doc({"doctype": "Evaluation Assignment", "appraisal_cycle": appraisal_doc.appraisal_cycle, "appraisal": appraisal_doc.name, "evaluation_type": policy.name, "employee": appraisal_doc.employee, "reviewer": reviewer, "evaluation_source": source.source, "assigned_on": today(), "due_date": add_days(today(), policy.due_days)})
            assignment.insert(ignore_permissions=True)
            created.append(assignment.name)
    _update_assignment_summary(appraisal_doc.name)
    return {"created": created, "existing": existing, "unresolved": unresolved}


def create_feedback(assignment_name):
    assignment = frappe.get_doc("Evaluation Assignment", assignment_name)
    assignment.check_permission("write")
    if assignment.feedback and frappe.db.exists("Employee Performance Feedback", assignment.feedback):
        return {"feedback": assignment.feedback, "existing": True}
    if assignment.status not in {"Assigned", "In Progress"}:
        frappe.throw(_("Feedback cannot be created for assignment status {0}.").format(assignment.status))
    feedback = frappe.new_doc("Employee Performance Feedback")
    values = {"employee": assignment.employee, "reviewer": assignment.reviewer, "user": assignment.reviewer_user, "appraisal_cycle": assignment.appraisal_cycle, "appraisal": assignment.appraisal, "qorg_assignment": assignment.name, "qorg_evaluation_source": assignment.evaluation_source, "qorg_anonymous": assignment.anonymous, "qorg_weight": assignment.weight}
    for fieldname, value in values.items():
        if feedback.meta.has_field(fieldname):
            feedback.set(fieldname, value)
    feedback.insert(ignore_permissions=True)
    frappe.db.set_value("Evaluation Assignment", assignment.name, {"feedback": feedback.name, "status": "In Progress"}, update_modified=True)
    return {"feedback": feedback.name, "existing": False}


def replace_assignment(name, reviewer, reason):
    old = frappe.get_doc("Evaluation Assignment", name)
    old.check_permission("write")
    if old.status in {"Submitted", "Replaced", "Cancelled"}:
        frappe.throw(_("This assignment cannot be replaced."))
    if not (reason or "").strip():
        frappe.throw(_("Replacement reason is required."))
    new = frappe.copy_doc(old)
    new.name = None
    new.reviewer = reviewer
    new.feedback = None
    new.status = "Assigned"
    new.locked = 0
    new.replaces_assignment = old.name
    new.replaced_by = None
    new.replacement_reason = reason
    new.insert(ignore_permissions=True)
    old.flags.evaluation_status_transition = True
    old.status = "Replaced"
    old.locked = 1
    old.replaced_by = new.name
    old.replacement_reason = reason
    old.save(ignore_permissions=True)
    return {"old": old.name, "new": new.name}


def decline_assignment(name, reason, conflict=False):
    doc = frappe.get_doc("Evaluation Assignment", name)
    doc.check_permission("write")
    if doc.status not in {"Assigned", "In Progress"}:
        frappe.throw(_("This assignment cannot be declined."))
    if not (reason or "").strip():
        frappe.throw(_("Decline reason is required."))
    doc.flags.evaluation_status_transition = True
    doc.status = "Declined"
    doc.decline_reason = reason
    doc.conflict_declared = 1 if conflict else doc.conflict_declared
    if conflict and not doc.conflict_notes:
        doc.conflict_notes = reason
    doc.locked = 1
    doc.save(ignore_permissions=True)
    _update_assignment_summary(doc.appraisal)
    return {"name": doc.name, "status": doc.status}


def validate_appraisal_cycle(doc, method=None):
    previous = doc.get_doc_before_save()
    if not doc.get("qorg_evaluation_type"):
        return
    policy = frappe.get_doc("Evaluation Type", doc.qorg_evaluation_type)
    if not policy.active:
        frappe.throw(_("Evaluation Type is inactive."))
    appraisals_exist = False if doc.is_new() else bool(frappe.db.exists("Appraisal", {"appraisal_cycle": doc.name}))
    if previous and appraisals_exist and previous.get("qorg_evaluation_type") != doc.qorg_evaluation_type:
        frappe.throw(_("Evaluation Type cannot change after Appraisals exist."))
    if not doc.get("qorg_policy_snapshot") or (previous and previous.get("qorg_evaluation_type") != doc.qorg_evaluation_type and not appraisals_exist):
        doc.qorg_policy_snapshot = json.dumps(_policy_snapshot(policy), ensure_ascii=False, default=str)


def validate_appraisal(doc, method=None):
    if not doc.appraisal_cycle:
        return
    evaluation_type = frappe.db.get_value("Appraisal Cycle", doc.appraisal_cycle, "qorg_evaluation_type")
    if evaluation_type:
        doc.qorg_evaluation_type = evaluation_type


def _policy_snapshot(policy):
    return {
        "evaluation_type": policy.name,
        "rating_scale": policy.rating_scale,
        "completion_policy": policy.completion_policy,
        "min_completion": policy.min_completion,
        "due_days": policy.due_days,
        "source_score_max": policy.source_score_max,
        "confidentiality": policy.confidentiality,
        "self_required": policy.self_required,
        "goals_included": policy.goals_included,
        "competencies_included": policy.competencies_included,
        "sources": [{field: row.get(field) for field in ("source", "weight", "required_reviewers", "min_reviews", "include_score", "anonymous", "assignment_required", "assignment_strategy", "criteria_set", "missing_policy", "comments_below", "evidence_below")} for row in policy.sources],
    }


def validate_feedback(doc, method=None):
    if not doc.get("qorg_assignment"):
        return
    assignment = frappe.get_doc("Evaluation Assignment", doc.qorg_assignment)
    if assignment.feedback and assignment.feedback != doc.name:
        frappe.throw(_("Assignment is already linked to another Feedback."))
    expected = {"employee": assignment.employee, "reviewer": assignment.reviewer, "appraisal_cycle": assignment.appraisal_cycle, "appraisal": assignment.appraisal}
    for fieldname, value in expected.items():
        if doc.get(fieldname) != value:
            frappe.throw(_("Feedback {0} must match the Evaluation Assignment.").format(doc.meta.get_label(fieldname)))
    if frappe.session.user not in {assignment.reviewer_user, "Administrator"} and not {"HR Manager", "System Manager"}.intersection(frappe.get_roles()):
        frappe.throw(_("Only the assigned reviewer can edit this feedback."), frappe.PermissionError)


def feedback_submitted(doc, method=None):
    if not doc.get("qorg_assignment"):
        return
    assignment = frappe.get_doc("Evaluation Assignment", doc.qorg_assignment)
    frappe.db.set_value("Evaluation Assignment", assignment.name, {"status": "Submitted", "submitted_on": now_datetime(), "locked": 1, "feedback": doc.name}, update_modified=True)
    _update_assignment_summary(assignment.appraisal)


def feedback_cancelled(doc, method=None):
    if not doc.get("qorg_assignment"):
        return
    assignment = frappe.get_doc("Evaluation Assignment", doc.qorg_assignment)
    frappe.db.set_value("Evaluation Assignment", assignment.name, {"status": "In Progress", "submitted_on": None, "locked": 0}, update_modified=True)
    _update_assignment_summary(assignment.appraisal)


def _resolve_reviewers(appraisal, source, manual):
    if source.source == "Self":
        return [appraisal.employee]
    employee = frappe.get_doc("Employee", appraisal.employee)
    if source.assignment_strategy == "Direct Supervisor":
        return [employee.reports_to] if employee.reports_to else []
    if source.assignment_strategy == "Direct Reports":
        return frappe.get_all("Employee", filters={"reports_to": appraisal.employee, "status": "Active"}, pluck="name", order_by="name")
    if source.assignment_strategy == "Department Head" and employee.department:
        head = frappe.db.get_value("Department", employee.department, "department_head") if frappe.get_meta("Department").has_field("department_head") else None
        return [head] if head and frappe.db.exists("Employee", head) else []
    return list(dict.fromkeys(manual))


def _update_assignment_summary(appraisal):
    rows = frappe.get_all("Evaluation Assignment", filters={"appraisal": appraisal, "status": ["not in", ["Replaced", "Cancelled"]]}, fields=["status"])
    values = {"qorg_assignment_total": len(rows), "qorg_assignment_submitted": sum(1 for row in rows if row.status == "Submitted"), "qorg_assignment_pending": sum(1 for row in rows if row.status in {"Assigned", "In Progress"})}
    meta = frappe.get_meta("Appraisal")
    values = {field: value for field, value in values.items() if meta.has_field(field)}
    if values:
        frappe.db.set_value("Appraisal", appraisal, values, update_modified=False)

STAGES = ("Preparation", "Goal Setting", "Goal Tracking", "Self-Appraisal Open", "Feedback Collection", "HR Review", "Finalized", "Closed", "Reopened", "Cancelled")
STAGE_TRANSITIONS = {
    "Preparation": {"Goal Setting"},
    "Goal Setting": {"Goal Tracking", "Cancelled"},
    "Goal Tracking": {"Self-Appraisal Open", "Feedback Collection", "Cancelled"},
    "Self-Appraisal Open": {"Feedback Collection", "Goal Tracking", "Cancelled"},
    "Feedback Collection": {"HR Review", "Self-Appraisal Open", "Cancelled"},
    "HR Review": {"Finalized", "Feedback Collection", "Cancelled"},
    "Finalized": {"Reopened"},
    "Reopened": {"HR Review", "Cancelled"},
    "Closed": set(),
    "Cancelled": set(),
}
CALC_FIELDS = ("qorg_completion", "qorg_final_score", "qorg_rating", "qorg_outcome", "qorg_provisional", "qorg_source_results", "qorg_calc_snapshot")


def recalculate_appraisal(appraisal_name, save=True):
    doc = frappe.get_doc("Appraisal", appraisal_name)
    doc.check_permission("write")
    if doc.get("qorg_stage") in {"Closed", "Cancelled"}:
        frappe.throw(_("A Closed or Cancelled Appraisal cannot be recalculated."))
    policy = _appraisal_policy(doc)
    result = _calculate(doc, policy)
    doc.set("qorg_source_results", [])
    for row in result["sources"]:
        doc.append("qorg_source_results", row)
    doc.qorg_completion = result["completion"]
    doc.qorg_final_score = result["final_score"]
    doc.qorg_rating = result["rating"]
    doc.qorg_outcome = result["outcome"]
    doc.qorg_provisional = 1 if result["provisional"] else 0
    doc.qorg_calc_snapshot = json.dumps(result, ensure_ascii=False, default=str)
    doc.qorg_calculated_by = frappe.session.user
    doc.qorg_calculated_on = now_datetime()
    revision = len(doc.get("qorg_calc_log") or []) + 1
    doc.append("qorg_calc_log", {"revision": revision, "calculated_on": doc.qorg_calculated_on, "calculated_by": frappe.session.user, "completion": result["completion"], "final_score": result["final_score"], "rating": result["rating"], "outcome": result["outcome"], "provisional": result["provisional"], "snapshot": doc.qorg_calc_snapshot})
    if save:
        doc.flags.qorg_calculation_write = True
        doc.save(ignore_permissions=True)
    return result


def transition_appraisal(name, target, reason=None):
    doc = frappe.get_doc("Appraisal", name)
    doc.check_permission("write")
    current = doc.get("qorg_stage") or "Preparation"
    if target not in STAGES or target not in STAGE_TRANSITIONS.get(current, set()):
        frappe.throw(_("Transition from {0} to {1} is not allowed.").format(current, target))
    _authorize_stage(target)
    if target in {"Reopened", "Cancelled"} and not (reason or "").strip():
        frappe.throw(_("A reason is required."))
    if target == "Finalized":
        result = recalculate_appraisal(doc.name, save=False)
        if result["provisional"] or result["completion"] < 100:
            frappe.throw(_("Only a complete, non-provisional calculation can be Finalized."))
        if result["outcome"] == "Development Plan" and not _has_development_action(doc.employee, doc.name):
            frappe.throw(_("A Development Action is required before finalizing this outcome."))
        doc.qorg_finalized_by = frappe.session.user
        doc.qorg_finalized_on = now_datetime()
    if target == "Reopened":
        doc.qorg_reopen_reason = reason
        doc.qorg_reopened_by = frappe.session.user
        doc.qorg_reopened_on = now_datetime()
    if target == "Cancelled":
        doc.qorg_cancel_reason = reason
    doc.qorg_stage = target
    doc.qorg_stage_by = frappe.session.user
    doc.qorg_stage_on = now_datetime()
    doc.flags.qorg_stage_transition = True
    doc.flags.qorg_calculation_write = True
    doc.save(ignore_permissions=True)
    return {"name": doc.name, "stage": target}


def protect_appraisal(doc, method=None):
    previous = doc.get_doc_before_save()
    validate_appraisal(doc, method)
    if not doc.get("qorg_stage"):
        doc.qorg_stage = "Preparation"
    if not previous:
        return
    if previous.get("qorg_stage") != doc.get("qorg_stage") and not doc.flags.get("qorg_stage_transition"):
        frappe.throw(_("Use Appraisal lifecycle actions to change Evaluation Stage."))
    if previous.get("qorg_stage") in {"Finalized", "Closed"} and not doc.flags.get("qorg_stage_transition"):
        protected = ("employee", "appraisal_cycle", "appraisal_template", "goals", "self_ratings", "reflections") + CALC_FIELDS
        if any(_normalized(doc.get(field)) != _normalized(previous.get(field)) for field in protected):
            frappe.throw(_("Finalized Appraisal content and results are protected. Reopen it first."))
    if not doc.flags.get("qorg_calculation_write"):
        for field in CALC_FIELDS:
            if _normalized(doc.get(field)) != _normalized(previous.get(field)):
                frappe.throw(_("Calculated appraisal fields are system controlled."))


def _calculate(doc, policy):
    source_defs = {row.source: row for row in policy.sources if row.include_score}
    rows = []
    for source, definition in source_defs.items():
        rows.append(_source_result(doc, policy, definition))
    completed_original_weight = sum(flt(row["weight"]) for row in rows if row["status"] == "Complete")
    total_original_weight = sum(flt(row["weight"]) for row in rows)
    global_policy = policy.completion_policy
    strict_blocked = any(row["status"] != "Complete" and row["policy_applied"] == "Strict Completion" for row in rows)
    completion = 100 * completed_original_weight / total_original_weight if total_original_weight else 0
    provisional = False
    denominator = total_original_weight
    if global_policy == "Strict Completion" and strict_blocked:
        provisional = True
    elif global_policy == "Completed Weight":
        denominator = completed_original_weight
        provisional = completion < 100
    elif global_policy == "Reallocate Weight":
        denominator = completed_original_weight
        provisional = completion < 100
    final_score = 0
    for row in rows:
        if row["status"] != "Complete" or not denominator:
            row["effective_weight"] = 0
            row["weighted_score"] = 0
            continue
        if global_policy == "Completed Weight":
            # Completed Weight normalizes the score denominator while preserving original source weights in the audit row.
            row["effective_weight"] = flt(row["weight"])
            row["weighted_score"] = flt(row["source_score"]) * flt(row["weight"]) / denominator
        elif global_policy == "Reallocate Weight":
            # Reallocate Weight explicitly produces new effective weights totaling 100 across completed sources.
            row["effective_weight"] = flt(row["weight"]) * 100 / denominator
            row["weighted_score"] = flt(row["source_score"]) * flt(row["effective_weight"]) / 100
        else:
            row["effective_weight"] = flt(row["weight"])
            row["weighted_score"] = flt(row["source_score"]) * flt(row["effective_weight"]) / 100
        final_score += row["weighted_score"]
    if completion < flt(policy.min_completion):
        provisional = True
    rating, outcome, development = _rating(policy.rating_scale, final_score)
    if global_policy == "Strict Completion" and strict_blocked:
        outcome = "Incomplete"
    return {"appraisal": doc.name, "evaluation_type": policy.name, "policy": global_policy, "completion": completion, "final_score": final_score, "rating": rating, "outcome": outcome, "development_required": development, "provisional": provisional, "sources": rows, "calculated_on": now_datetime(), "calculated_by": frappe.session.user}


def _source_result(doc, policy, definition):
    source = definition.source
    expected = definition.min_reviews if definition.assignment_required else 1
    completed, scores = 0, []
    if source == "Goals":
        score = flt(doc.get("total_score") or doc.get("goal_score_percentage"))
        if score or doc.get("total_score") == 0:
            scores = [score]
            completed = 1
    elif source == "Self":
        score = flt(doc.get("self_score"))
        if score or doc.get("self_score") == 0:
            scores = [score]
            completed = 1
    else:
        assignments = frappe.get_all("Evaluation Assignment", filters={"appraisal": doc.name, "evaluation_source": source, "status": "Submitted"}, fields=["feedback"])
        for assignment in assignments:
            if assignment.feedback:
                score = frappe.db.get_value("Employee Performance Feedback", assignment.feedback, "total_score")
                if score is not None:
                    scores.append(flt(score))
        completed = len(scores)
    status = "Complete" if completed >= expected else ("Partial" if completed else "Missing")
    raw_score = sum(scores) / len(scores) if scores else 0
    score = _normalize_source_score(raw_score, policy.source_score_max)
    applied_policy = definition.missing_policy if definition.missing_policy != "Use Evaluation Policy" else policy.completion_policy
    return {"source": source, "weight": definition.weight, "expected_reviews": expected, "completed_reviews": completed, "completion": min(100, completed * 100 / expected) if expected else 100, "source_score": score, "effective_weight": 0, "weighted_score": 0, "status": status, "policy_applied": applied_policy, "notes": ""}


def _normalize_source_score(score, maximum):
    maximum = flt(maximum)
    if maximum <= 0:
        frappe.throw(_("Source Score Maximum must be greater than zero."))
    if flt(score) < 0 or flt(score) > maximum:
        frappe.throw(_("Raw source score {0} is outside the configured 0 to {1} range.").format(score, maximum))
    return flt(score) * 100 / maximum


def _appraisal_policy(doc):
    name = doc.get("qorg_evaluation_type") or frappe.db.get_value("Appraisal Cycle", doc.appraisal_cycle, "qorg_evaluation_type")
    if not name:
        frappe.throw(_("Evaluation Type is required."))
    return frappe.get_doc("Evaluation Type", name)


def _rating(scale_name, score):
    scale = frappe.get_doc("Rating Scale", scale_name)
    for band in scale.bands:
        if flt(band.min_score) <= flt(score) <= flt(band.max_score):
            return band.rating, band.outcome, bool(band.development_required)
    frappe.throw(_("No Rating Band matches score {0}.").format(score))


def _authorize_stage(target):
    roles = set(frappe.get_roles())
    if target in {"Finalized", "Closed", "Reopened", "Cancelled"} and not {"HR Manager", "System Manager"}.intersection(roles):
        frappe.throw(_("HR Manager role is required for this transition."), frappe.PermissionError)
    if target in {"Goal Setting", "Goal Tracking", "Self-Appraisal Open", "Feedback Collection", "HR Review"} and not {"HR User", "HR Manager", "System Manager"}.intersection(roles):
        frappe.throw(_("HR role is required for this transition."), frappe.PermissionError)


def _has_development_action(employee, appraisal):
    return bool(frappe.db.exists("Development Action", {"employee": employee, "source_type": "Appraisal", "source_doctype": "Appraisal", "source_document": appraisal, "status": ["not in", ["Cancelled"]]}))


def _normalized(value):
    if hasattr(value, "as_dict"):
        return value.as_dict()
    if isinstance(value, list):
        return [row.as_dict() if hasattr(row, "as_dict") else row for row in value]
    return value


def before_submit_appraisal(doc, method=None):
    if doc.get("qorg_stage") != "Finalized":
        frappe.throw(_("Appraisal must be Finalized before submission."))
    result = recalculate_appraisal(doc.name, save=False)
    if result["provisional"] or result["completion"] < 100:
        frappe.throw(_("Submitted Appraisal requires a complete, non-provisional calculation."))


def appraisal_submitted(doc, method=None):
    frappe.db.set_value("Appraisal", doc.name, {"qorg_stage": "Closed", "qorg_stage_by": frappe.session.user, "qorg_stage_on": now_datetime()}, update_modified=False)


def appraisal_cancelled(doc, method=None):
    frappe.db.set_value("Appraisal", doc.name, {"qorg_stage": "Cancelled", "qorg_stage_by": frappe.session.user, "qorg_stage_on": now_datetime(), "qorg_cancel_reason": _("Standard Appraisal document cancelled.")}, update_modified=False)

# Calculation hardening: source-specific scales, review thresholds, anonymity,
# missing-source policies, flexible minimum completion and protected feedback.
def validate_evaluation_type(doc):
    if not doc.sources:
        frappe.throw(_("At least one Evaluation Source is required."))
    if flt(doc.source_score_max) <= 0:
        frappe.throw(_("Source Score Maximum must be greater than zero."))
    if not 0 <= flt(doc.min_completion) <= 100:
        frappe.throw(_("Minimum Completion must be between 0 and 100."))
    seen, included_weight = set(), Decimal("0")
    for row in doc.sources:
        if row.source not in SOURCES or row.source in seen:
            frappe.throw(_("Invalid or duplicate Evaluation Source: {0}.").format(row.source))
        seen.add(row.source)
        if row.source in {"Goals", "Self"}:
            row.assignment_required = 0
            row.required_reviewers = row.min_reviews = 1
        if row.required_reviewers < 1 or row.min_reviews < 1 or row.min_reviews > row.required_reviewers:
            frappe.throw(_("Reviewer counts are invalid for {0}.").format(row.source))
        if row.source == "Direct Manager" and row.assignment_strategy not in {"Direct Supervisor", "Manual"}:
            frappe.throw(_("Direct Manager must use Direct Supervisor or Manual assignment."))
        if row.score_type == "Numeric Scale" and flt(row.score_max or doc.source_score_max) <= 0:
            frappe.throw(_("Score Maximum must be greater than zero for {0}.").format(row.source))
        if row.score_type == "Pass/Fail" and flt(row.pass_score) < 0:
            frappe.throw(_("Pass Score cannot be negative."))
        if row.anonymous:
            minimum_group = max(2, int(row.min_anonymous_group or 3))
            if row.required_reviewers < minimum_group or row.min_reviews < minimum_group:
                frappe.throw(_("Anonymous source {0} requires at least {1} required and completed reviewers.").format(row.source, minimum_group))
        if row.include_score:
            included_weight += Decimal(str(flt(row.weight)))
        elif flt(row.weight):
            frappe.throw(_("Excluded source {0} must have zero weight.").format(row.source))
    if included_weight != Decimal("100"):
        frappe.throw(_("Included Evaluation Source weights must total 100%; current total is {0}.").format(included_weight))
    if doc.self_required and "Self" not in seen:
        frappe.throw(_("Self-Appraisal Required needs a Self evaluation source."))
    if not frappe.db.exists("Rating Scale", doc.rating_scale):
        frappe.throw(_("Rating Scale does not exist."))


def _policy_snapshot(policy):
    fields = ("source", "weight", "required_reviewers", "min_reviews", "include_score", "anonymous", "min_anonymous_group", "assignment_required", "assignment_strategy", "criteria_set", "missing_policy", "score_type", "score_max", "pass_score", "comments_below", "evidence_below")
    return {"evaluation_type": policy.name, "rating_scale": policy.rating_scale, "completion_policy": policy.completion_policy, "min_completion": policy.min_completion, "due_days": policy.due_days, "source_score_max": policy.source_score_max, "confidentiality": policy.confidentiality, "self_required": policy.self_required, "goals_included": policy.goals_included, "competencies_included": policy.competencies_included, "sources": [{field: row.get(field) for field in fields} for row in policy.sources]}


def validate_feedback(doc, method=None):
    if not doc.get("qorg_assignment"):
        return
    assignment = frappe.get_doc("Evaluation Assignment", doc.qorg_assignment)
    appraisal = frappe.get_doc("Appraisal", assignment.appraisal)
    if appraisal.get("qorg_stage") in {"Finalized", "Closed"}:
        frappe.throw(_("Feedback cannot change after the Appraisal is Finalized. Reopen the Appraisal first."))
    if assignment.feedback and assignment.feedback != doc.name:
        frappe.throw(_("Assignment is already linked to another Feedback."))
    for fieldname, value in {"employee": assignment.employee, "reviewer": assignment.reviewer, "appraisal_cycle": assignment.appraisal_cycle, "appraisal": assignment.appraisal}.items():
        if doc.get(fieldname) != value:
            frappe.throw(_("Feedback {0} must match the Evaluation Assignment.").format(doc.meta.get_label(fieldname)))
    if frappe.session.user not in {assignment.reviewer_user, "Administrator"} and not {"HR Manager", "System Manager"}.intersection(frappe.get_roles()):
        frappe.throw(_("Only the assigned reviewer can edit this feedback."), frappe.PermissionError)
    policy = frappe.get_doc("Evaluation Type", assignment.evaluation_type)
    definition = next(row for row in policy.sources if row.source == assignment.evaluation_source)
    normalized = _normalize_by_definition(flt(doc.total_score), definition, policy)
    comments = (doc.get("qorg_comments") or doc.get("feedback") or "").strip()
    if definition.comments_below is not None and flt(definition.comments_below) > 0 and normalized < flt(definition.comments_below) and not comments:
        frappe.throw(_("Feedback comments are required below {0}% for source {1}.").format(definition.comments_below, definition.source))
    if definition.evidence_below is not None and flt(definition.evidence_below) > 0 and normalized < flt(definition.evidence_below) and not doc.get("qorg_evidence"):
        frappe.throw(_("Evidence is required below {0}% for source {1}.").format(definition.evidence_below, definition.source))


def feedback_cancelled(doc, method=None):
    if not doc.get("qorg_assignment"):
        return
    assignment = frappe.get_doc("Evaluation Assignment", doc.qorg_assignment)
    appraisal = frappe.get_doc("Appraisal", assignment.appraisal)
    if appraisal.get("qorg_stage") in {"Finalized", "Closed"}:
        frappe.throw(_("Feedback cannot be cancelled after the Appraisal is Finalized. Reopen it first."))
    frappe.db.set_value("Evaluation Assignment", assignment.name, {"status": "In Progress", "submitted_on": None, "locked": 0}, update_modified=True)
    _update_assignment_summary(assignment.appraisal)


def _calculate(doc, policy):
    rows = [_source_result(doc, policy, definition) for definition in policy.sources]
    included = [row for row in rows if row["status"] != "Excluded"]
    total_weight = sum(flt(row["weight"]) for row in included)
    operational_completion = sum(flt(row["weight"]) * flt(row["completion"]) / 100 for row in included) / total_weight * 100 if total_weight else 100
    eligible = [row for row in included if row["meets_minimum"]]
    eligible_weight = sum(flt(row["weight"]) for row in eligible)
    strict_blocked = any(not row["meets_minimum"] and row["policy_applied"] == "Strict Completion" for row in included)
    flexible = policy.completion_policy in {"Completed Weight", "Reallocate Weight"}
    provisional = strict_blocked or operational_completion < flt(policy.min_completion) or not eligible_weight
    final_score = 0
    for row in rows:
        row["effective_weight"] = row["weighted_score"] = 0
        if row["status"] == "Excluded" or not row["meets_minimum"]:
            continue
        applied = row["policy_applied"]
        if policy.completion_policy == "Reallocate Weight" or applied == "Reallocate Weight":
            row["effective_weight"] = flt(row["weight"]) * 100 / eligible_weight
            row["weighted_score"] = flt(row["source_score"]) * row["effective_weight"] / 100
        elif policy.completion_policy == "Completed Weight" or applied == "Completed Weight":
            row["effective_weight"] = flt(row["weight"])
            row["weighted_score"] = flt(row["source_score"]) * flt(row["weight"]) / eligible_weight
        else:
            row["effective_weight"] = flt(row["weight"])
            row["weighted_score"] = flt(row["source_score"]) * row["effective_weight"] / 100
        final_score += row["weighted_score"]
    rating, outcome, development = _rating(policy.rating_scale, final_score)
    if strict_blocked:
        outcome = "Incomplete"
        provisional = True
    return {"appraisal": doc.name, "evaluation_type": policy.name, "policy": policy.completion_policy, "minimum_completion": policy.min_completion, "completion": operational_completion, "eligible_weight": eligible_weight, "final_score": final_score, "rating": rating, "outcome": outcome, "development_required": development, "provisional": provisional, "sources": rows, "calculated_on": now_datetime(), "calculated_by": frappe.session.user}


def _source_result(doc, policy, definition):
    source = definition.source
    required = int(definition.required_reviewers or 1) if definition.assignment_required else 1
    minimum = int(definition.min_reviews or 1) if definition.assignment_required else 1
    scores = []
    if source == "Goals":
        goal_rows = list(doc.get("goals") or doc.get("appraisal_kra") or [])
        if goal_rows:
            raw = doc.get("total_score") if doc.get("total_score") is not None else doc.get("goal_score_percentage")
            if raw is not None:
                scores = [flt(raw)]
    elif source == "Self":
        if list(doc.get("self_ratings") or []):
            raw = doc.get("self_score")
            if raw is not None:
                scores = [flt(raw)]
    else:
        assignments = frappe.get_all("Evaluation Assignment", filters={"appraisal": doc.name, "evaluation_source": source, "status": "Submitted"}, fields=["feedback"])
        for assignment in assignments:
            if assignment.feedback:
                raw = frappe.db.get_value("Employee Performance Feedback", assignment.feedback, "total_score")
                if raw is not None:
                    scores.append(flt(raw))
    completed = len(scores)
    anonymous_minimum = max(2, int(definition.min_anonymous_group or 3)) if definition.anonymous else 0
    meets = completed >= minimum and (not definition.anonymous or completed >= anonymous_minimum)
    completion = min(100, completed * 100 / required) if required else 100
    raw_score = sum(scores) / len(scores) if scores else 0
    normalized = _normalize_by_definition(raw_score, definition, policy) if scores else 0
    applied = definition.missing_policy if definition.missing_policy != "Use Evaluation Policy" else policy.completion_policy
    if not definition.include_score:
        status = "Excluded"
    elif meets:
        status = "Complete"
    else:
        status = "Partial" if completed else "Missing"
    note = ""
    if definition.anonymous and completed < anonymous_minimum:
        note = _("Anonymous minimum group size {0} not met.").format(anonymous_minimum)
    return {"source": source, "weight": definition.weight if definition.include_score else 0, "expected_reviews": required, "minimum_reviews": minimum, "completed_reviews": completed, "meets_minimum": 1 if meets else 0, "completion": completion, "raw_score": raw_score, "source_score": normalized, "effective_weight": 0, "weighted_score": 0, "status": status, "policy_applied": applied if definition.include_score else "Informational Only", "score_type": definition.score_type, "notes": note}


def _normalize_by_definition(score, definition, policy):
    kind = definition.score_type or "Numeric Scale"
    if kind == "Percentage":
        if not 0 <= flt(score) <= 100:
            frappe.throw(_("Percentage score must be between 0 and 100."))
        return flt(score)
    if kind == "Pass/Fail":
        return 100 if flt(score) >= flt(definition.pass_score) else 0
    return _normalize_source_score(score, definition.score_max or policy.source_score_max)


def transition_appraisal(name, target, reason=None):
    doc = frappe.get_doc("Appraisal", name)
    doc.check_permission("write")
    current = doc.get("qorg_stage") or "Preparation"
    if target not in STAGES or target not in STAGE_TRANSITIONS.get(current, set()):
        frappe.throw(_("Transition from {0} to {1} is not allowed.").format(current, target))
    _authorize_stage(target)
    if target in {"Reopened", "Cancelled"} and not (reason or "").strip():
        frappe.throw(_("A reason is required."))
    if target == "Finalized":
        result = recalculate_appraisal(doc.name, save=False)
        if result["provisional"] or result["completion"] < flt(_appraisal_policy(doc).min_completion):
            frappe.throw(_("The appraisal does not meet the configured completion policy."))
        if result["outcome"] == "Development Plan" and not _has_development_action(doc.employee, doc.name):
            frappe.throw(_("A Development Action is required before finalizing this outcome."))
        doc.qorg_finalized_by, doc.qorg_finalized_on = frappe.session.user, now_datetime()
    if target == "Reopened":
        doc.qorg_reopen_reason, doc.qorg_reopened_by, doc.qorg_reopened_on = reason, frappe.session.user, now_datetime()
    if target == "Cancelled":
        doc.qorg_cancel_reason = reason
    doc.qorg_stage, doc.qorg_stage_by, doc.qorg_stage_on = target, frappe.session.user, now_datetime()
    doc.flags.qorg_stage_transition = doc.flags.qorg_calculation_write = True
    doc.save(ignore_permissions=True)
    return {"name": doc.name, "stage": target}


def before_submit_appraisal(doc, method=None):
    if doc.get("qorg_stage") != "Finalized":
        frappe.throw(_("Appraisal must be Finalized before submission."))
    result = recalculate_appraisal(doc.name, save=False)
    policy = _appraisal_policy(doc)
    if result["provisional"] or result["completion"] < flt(policy.min_completion):
        frappe.throw(_("Submitted Appraisal does not meet the configured completion policy."))
