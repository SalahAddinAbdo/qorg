from __future__ import annotations

import json
import frappe
from frappe import _
from frappe.utils import add_days, flt, getdate, now_datetime, today

ASSESS_EDITABLE = {"Draft"}
FOLLOW_EDITABLE = {"Open", "In Progress", "Overdue"}


def validate_assessment(doc):
    previous = doc.get_doc_before_save()
    _validate_event_employee(doc.training_event, doc.employee)
    event = frappe.get_doc("Training Event", doc.training_event)
    _validate_assessment_window(doc, event)
    _validate_assessment_attempt(doc)
    maximum = flt(doc.maximum_score)
    score = flt(doc.score)
    if maximum <= 0:
        frappe.throw(_("Maximum Score must be greater than zero."))
    if score < 0 or score > maximum:
        frappe.throw(_("Score must be between zero and Maximum Score."))
    doc.percentage = score * 100 / maximum
    doc.passed = 1 if doc.percentage >= flt(doc.passing_percentage) else 0
    if previous:
        if previous.status != doc.status and not doc.flags.get("training_status_transition"):
            frappe.throw(_("Use the assessment actions to change Status."))
        if previous.status in {"Submitted", "Cancelled"}:
            changed = [field for field in ("training_event", "employee", "assessment_type", "attempt_no", "maximum_score", "score", "passing_percentage", "evidence") if doc.get(field) != previous.get(field)]
            if changed:
                frappe.throw(_("Submitted or cancelled assessment values cannot be changed."))


def validate_follow_up(doc):
    previous = doc.get_doc_before_save()
    _validate_event_employee(doc.training_event, doc.employee)
    if doc.training_result:
        linked_event = frappe.db.get_value("Training Result", doc.training_result, "training_event")
        if linked_event and linked_event != doc.training_event:
            frappe.throw(_("Training Result must belong to the selected Training Event."))
    if doc.due_date and getdate(doc.due_date) < getdate(today()) and doc.status in {"Open", "In Progress"}:
        doc.status = "Overdue"
    if doc.status == "Completed":
        if not doc.application_level or not doc.performance_improvement or not (doc.follow_up_comments or "").strip():
            frappe.throw(_("Application Level, Performance Improvement, and Follow-up Comments are required."))
        if doc.evidence_type == "Employee Document Record" and not doc.evidence_document:
            frappe.throw(_("Evidence Document is required."))
        if doc.evidence_type == "External URL" and not doc.evidence_url:
            frappe.throw(_("Evidence URL is required."))
        if not doc.completed_by:
            doc.completed_by = frappe.session.user
        if not doc.completed_on:
            doc.completed_on = now_datetime()
    if previous:
        if previous.status == "Completed" and doc.status != "Completed":
            frappe.throw(_("A completed follow-up cannot be reopened directly."))
        if previous.status == "Cancelled" and doc.status != "Cancelled":
            frappe.throw(_("A cancelled follow-up cannot be reopened."))
    if doc.additional_training_required and not doc.recommended_action:
        frappe.throw(_("Recommended Development Action is required when additional training is required."))
    if doc.additional_training_required and doc.recommended_action:
        action = frappe.get_doc("Development Action", doc.recommended_action)
        if action.employee != doc.employee or action.source_type != "Training Follow-up":
            frappe.throw(_("Recommended Development Action must belong to the employee and use Training Follow-up as source."))


def submit_assessment(name):
    doc = frappe.get_doc("Training Assessment", name)
    doc.check_permission("write")
    if doc.status == "Submitted":
        return {"name": doc.name, "status": doc.status, "already_submitted": True}
    if doc.status != "Draft":
        frappe.throw(_("Only a Draft assessment can be submitted."))
    doc.status = "Submitted"
    doc.submitted_by = frappe.session.user
    doc.submitted_on = now_datetime()
    doc.flags.training_status_transition = True
    doc.save()
    sync_training_result(doc.training_event)
    return {"name": doc.name, "status": doc.status}


def cancel_assessment(name, reason):
    doc = frappe.get_doc("Training Assessment", name)
    doc.check_permission("write")
    if doc.status != "Submitted":
        frappe.throw(_("Only a Submitted assessment can be cancelled."))
    if not (reason or "").strip():
        frappe.throw(_("Cancellation reason is required."))
    doc.status = "Cancelled"
    doc.cancelled_by = frappe.session.user
    doc.cancelled_on = now_datetime()
    doc.cancel_reason = reason
    doc.flags.training_status_transition = True
    doc.save()
    sync_training_result(doc.training_event)
    return {"name": doc.name, "status": doc.status}


def sync_training_result(training_event):
    result_name = frappe.db.get_value("Training Result", {"training_event": training_event, "docstatus": ["<", 2]}, "name")
    if not result_name:
        return None
    result = frappe.get_doc("Training Result", result_name)
    event = frappe.get_doc("Training Event", training_event)
    attendance = {row.employee: row for row in event.employees}
    for row in result.employees:
        event_row = attendance.get(row.employee)
        pre = _latest_assessment(training_event, row.employee, "Pre-Assessment")
        post = _latest_assessment(training_event, row.employee, "Post-Assessment")
        values = {
            "qorg_attendance_percentage": _attendance_percentage(event_row),
            "qorg_pre_score": pre.percentage if pre else None,
            "qorg_post_score": post.percentage if post else None,
            "qorg_raw_improvement": (post.percentage - pre.percentage) if pre and post else None,
            "qorg_improvement_percentage": _improvement_percentage(pre, post),
            "qorg_final_score": post.percentage if post else (pre.percentage if pre else None),
            "qorg_result": _assessment_result(pre, post, event_row),
            "qorg_certificate_eligible": _certificate_eligible(event, event_row, post),
        }
        for fieldname, value in values.items():
            if row.meta.has_field(fieldname):
                row.set(fieldname, value)
    result.flags.ignore_validate_update_after_submit = True
    result.save(ignore_permissions=True)
    return result.name


def generate_follow_ups(training_event):
    event = frappe.get_doc("Training Event", training_event)
    if not event.meta.has_field("qorg_follow_up_required") or not event.qorg_follow_up_required:
        return {"created": [], "existing": []}
    due_days = event.qorg_follow_up_days or 30
    responsible = event.qorg_follow_up_user or frappe.session.user
    created, existing = [], []
    result_name = frappe.db.get_value("Training Result", {"training_event": event.name, "docstatus": ["<", 2]}, "name")
    for row in event.employees:
        if not _participant_completed(row):
            continue
        exists = frappe.db.get_value("Training Follow-up", {"training_event": event.name, "employee": row.employee, "status": ["!=", "Cancelled"]}, "name")
        if exists:
            existing.append(exists)
            continue
        doc = frappe.get_doc({"doctype": "Training Follow-up", "training_event": event.name, "training_result": result_name, "employee": row.employee, "due_date": add_days(event.end_time, due_days), "responsible_user": responsible, "created_from_event": 1})
        doc.insert(ignore_permissions=True)
        created.append(doc.name)
    return {"created": created, "existing": existing}


def update_overdue_follow_ups():
    if not frappe.db.exists("DocType", "Training Follow-up"):
        return
    names = frappe.get_all("Training Follow-up", filters={"status": ["in", ["Open", "In Progress"]], "due_date": ["<", today()]}, pluck="name")
    for name in names:
        frappe.db.set_value("Training Follow-up", name, "status", "Overdue", update_modified=False)


def _validate_event_employee(training_event, employee):
    event = frappe.get_doc("Training Event", training_event)
    if not any(row.employee == employee for row in event.employees):
        frappe.throw(_("Employee {0} is not a participant in this Training Event.").format(employee))


def _validate_assessment_window(doc, event):
    if doc.assessment_type == "Pre-Assessment" and event.start_time and getdate(doc.assessment_date) > getdate(event.start_time):
        frappe.throw(_("Pre-Assessment cannot be after the Training Event start."))
    if doc.assessment_type in {"Post-Assessment", "Practical", "Certification Exam"}:
        participant = next((row for row in event.employees if row.employee == doc.employee), None)
        if not _eligible_for_post(event, participant):
            frappe.throw(_("Employee is not eligible for this post-training assessment."))


def _validate_assessment_attempt(doc):
    duplicate = frappe.db.get_value("Training Assessment", {"training_event": doc.training_event, "employee": doc.employee, "assessment_type": doc.assessment_type, "attempt_no": doc.attempt_no, "status": ["!=", "Cancelled"], "name": ["!=", doc.name or ""]}, "name")
    if duplicate:
        frappe.throw(_("Assessment attempt already exists: {0}.").format(duplicate))


def _latest_assessment(event, employee, assessment_type):
    name = frappe.db.get_value("Training Assessment", {"training_event": event, "employee": employee, "assessment_type": assessment_type, "status": "Submitted"}, "name", order_by="attempt_no desc, assessment_date desc")
    return frappe.get_doc("Training Assessment", name) if name else None


def _attendance_percentage(row):
    if not row:
        return 0
    if row.meta.has_field("qorg_attendance_percentage") and row.qorg_attendance_percentage is not None:
        return flt(row.qorg_attendance_percentage)
    return 100 if row.attendance == "Present" or row.status in {"Attended", "Completed"} else 0


def _eligible_for_post(event, row):
    minimum = event.qorg_min_attendance if event.meta.has_field("qorg_min_attendance") else 75
    return bool(row and _attendance_percentage(row) >= flt(minimum))


def _participant_completed(row):
    return bool(row and (_attendance_percentage(row) > 0 or row.status in {"Attended", "Completed"}))


def _improvement_percentage(pre, post):
    if not pre or not post:
        return None
    if pre.percentage >= 100:
        return 0 if post.percentage <= pre.percentage else 100
    return (post.percentage - pre.percentage) * 100 / max(1, 100 - pre.percentage)


def _assessment_result(pre, post, row):
    if not row or _attendance_percentage(row) <= 0:
        return "Not Eligible"
    if post:
        return "Passed" if post.passed else "Failed"
    if pre:
        return "Pre-Assessment Only"
    return "Pending"


def _certificate_eligible(event, row, post):
    if not event.has_certificate:
        return 0
    if not _eligible_for_post(event, row):
        return 0
    if event.meta.has_field("qorg_post_assessment_required") and event.qorg_post_assessment_required:
        return 1 if post and post.passed else 0
    return 1

COMPONENT_ASSESSMENT = {
    "Post-Assessment": "Post-Assessment",
    "Practical": "Practical",
    "Trainer Evaluation": "Trainer Evaluation",
    "Certification Exam": "Certification Exam",
}


def validate_training_policy(doc, method=None):
    rules = list(doc.get("qorg_result_rules") or [])
    if doc.doctype == "Training Event" and not rules and doc.training_program:
        program = frappe.get_doc("Training Program", doc.training_program)
        doc.qorg_training_pass_score = program.get("qorg_training_pass_score") or 60
        for rule in program.get("qorg_result_rules") or []:
            doc.append("qorg_result_rules", {key: rule.get(key) for key in ("component", "weight", "required", "must_pass", "attempt_policy", "pass_score")})
        rules = list(doc.get("qorg_result_rules") or [])
    if not rules:
        return
    seen = set()
    total = 0
    for rule in rules:
        if rule.component in seen:
            frappe.throw(_("Duplicate training result component: {0}.").format(rule.component))
        seen.add(rule.component)
        if flt(rule.weight) < 0:
            frappe.throw(_("Training result component weights cannot be negative."))
        total += flt(rule.weight)
        if rule.component != "Attendance" and not rule.attempt_policy:
            frappe.throw(_("Attempt Policy is required for {0}.").format(rule.component))
    if abs(total - 100) > 0.001:
        frappe.throw(_("Training result component weights must total 100%; current total is {0}.").format(total))
    if not 0 <= flt(doc.get("qorg_training_pass_score") or 60) <= 100:
        frappe.throw(_("Final Passing Score must be between 0 and 100."))


def sync_training_result(training_event):
    result_name = frappe.db.get_value("Training Result", {"training_event": training_event, "docstatus": ["<", 2]}, "name")
    if not result_name:
        return None
    result, event = frappe.get_doc("Training Result", result_name), frappe.get_doc("Training Event", training_event)
    attendance = {row.employee: row for row in event.employees}
    rules = _event_rules(event)
    for row in result.employees:
        event_row = attendance.get(row.employee)
        pre = _selected_assessment(training_event, row.employee, "Pre-Assessment", "Latest Attempt", 0)
        selected = {}
        for rule in rules:
            if rule["component"] != "Attendance":
                selected[rule["component"]] = _selected_assessment(training_event, row.employee, COMPONENT_ASSESSMENT[rule["component"]], rule["attempt_policy"], rule["pass_score"])
        calculation = calculate_training_result(_attendance_percentage(event_row), rules, selected, flt(event.get("qorg_training_pass_score") or 60), _feedback_complete(training_event, row.employee), bool(event.get("qorg_feedback_required")))
        post = selected.get("Post-Assessment")
        values = {
            "qorg_attendance_percentage": _attendance_percentage(event_row),
            "qorg_pre_score": pre.percentage if pre else None,
            "qorg_post_score": post.percentage if post else None,
            "qorg_practical_score": _score(selected.get("Practical")),
            "qorg_trainer_score": _score(selected.get("Trainer Evaluation")),
            "qorg_cert_score": _score(selected.get("Certification Exam")),
            "qorg_assessment_completion": calculation["completion"],
            "qorg_raw_improvement": (post.percentage - pre.percentage) if pre and post else None,
            "qorg_improvement_percentage": _improvement_percentage(pre, post),
            "qorg_final_score": calculation["final_score"],
            "qorg_result": calculation["result"],
            "qorg_result_notes": calculation["notes"],
            "qorg_certificate_eligible": _certificate_eligible_hardened(event, event_row, calculation),
        }
        for fieldname, value in values.items():
            if row.meta.has_field(fieldname):
                row.set(fieldname, value)
    result.flags.ignore_validate_update_after_submit = True
    result.save(ignore_permissions=True)
    return result.name


def _event_rules(event):
    rows = list(event.get("qorg_result_rules") or [])
    if not rows:
        if event.get("qorg_post_assessment_required"):
            return [{"component": "Post-Assessment", "weight": 100, "required": 1, "must_pass": 1, "attempt_policy": "Latest Attempt", "pass_score": 60}]
        return [{"component": "Attendance", "weight": 100, "required": 1, "must_pass": 1, "attempt_policy": "Latest Attempt", "pass_score": flt(event.get("qorg_min_attendance") or 75)}]
    return [{key: row.get(key) for key in ("component", "weight", "required", "must_pass", "attempt_policy", "pass_score")} for row in rows]


def calculate_training_result(attendance, rules, selected, final_pass_score, feedback_complete=True, feedback_required=False):
    weighted, completed_weight, required_count, completed_required, blockers, notes = 0, 0, 0, 0, [], []
    for rule in rules:
        component = rule["component"]
        required = bool(rule.get("required"))
        if required:
            required_count += 1
        if component == "Attendance":
            score, passed, exists = flt(attendance), flt(attendance) >= flt(rule.get("pass_score") or 0), True
        else:
            item = selected.get(component)
            exists = item is not None
            score = _score(item) if exists else 0
            passed = bool(item and score >= flt(rule.get("pass_score") or 0))
        if required and exists:
            completed_required += 1
        if required and not exists:
            blockers.append(_("Missing required component: {0}").format(component))
        if rule.get("must_pass") and (not exists or not passed):
            blockers.append(_("Required pass not achieved: {0}").format(component))
        if exists:
            weighted += score * flt(rule.get("weight")) / 100
            completed_weight += flt(rule.get("weight"))
    completion = completed_required * 100 / required_count if required_count else 100
    if feedback_required and not feedback_complete:
        blockers.append(_("Required training feedback is missing."))
    if blockers:
        result = "Incomplete" if any("Missing" in str(x) or "feedback" in str(x).lower() for x in blockers) else "Failed"
    else:
        result = "Passed" if weighted >= flt(final_pass_score) else "Failed"
    return {"final_score": weighted, "completion": completion, "result": result, "passed": result == "Passed", "blockers": blockers, "notes": "; ".join(str(x) for x in blockers)}


def _selected_assessment(event, employee, assessment_type, policy, pass_score):
    names = frappe.get_all("Training Assessment", filters={"training_event": event, "employee": employee, "assessment_type": assessment_type, "status": "Submitted"}, fields=["name", "attempt_no", "assessment_date", "percentage", "passed"], order_by="attempt_no asc, assessment_date asc")
    if not names:
        return None
    if policy == "Best Attempt":
        chosen = max(names, key=lambda x: flt(x.percentage))
    elif policy == "First Passing Attempt":
        chosen = next((x for x in names if flt(x.percentage) >= flt(pass_score)), names[-1])
    elif policy == "Average of Attempts":
        average = sum(flt(x.percentage) for x in names) / len(names)
        return frappe._dict({"percentage": average, "passed": average >= flt(pass_score), "attempt_no": 0})
    else:
        chosen = names[-1]
    return frappe._dict(chosen)


def _score(item):
    return flt(item.percentage) if item else None


def _feedback_complete(event, employee):
    filters = {"training_event": event, "employee": employee}
    if frappe.get_meta("Training Feedback").is_submittable:
        filters["docstatus"] = 1
    else:
        filters["docstatus"] = ["<", 2]
    return bool(frappe.db.exists("Training Feedback", filters))


def _certificate_eligible_hardened(event, row, calculation):
    return 1 if event.has_certificate and _eligible_for_post(event, row) and calculation["passed"] else 0


def _improvement_percentage(pre, post):
    if not pre or not post:
        return None
    if flt(pre.percentage) >= 100:
        return flt(post.percentage) - flt(pre.percentage)
    return (flt(post.percentage) - flt(pre.percentage)) * 100 / max(1, 100 - flt(pre.percentage))
