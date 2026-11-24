from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.utils import getdate, now_datetime, today

NEED_EDITABLE = {"Draft", "Returned"}
NEED_FINAL = {"Rejected", "Converted", "Cancelled"}
SOURCE_DOCTYPE = {
    "Appraisal Recommendation": "Appraisal",
    "Competency Gap": "Employee Skill Map",
    "Policy or Compliance Requirement": "Employee Document Requirement",
    "Contract Requirement": "Contract Template",
}
ACTION_SOURCE_DOCTYPE = {
    "Appraisal": "Appraisal",
    "Skill Assessment": "Employee Skill Map",
    "Performance Feedback": "Employee Performance Feedback",
    "Training Follow-up": "Training Follow-up",
    "Manager Decision": "Employee",
    "Compliance Requirement": "Employee Document Requirement",
}


def validate_training_need(doc):
    previous = doc.get_doc_before_save()
    _validate_need_dates(doc)
    _validate_need_scope(doc)
    _validate_need_source(doc)
    _validate_need_funding(doc)
    _validate_participants(doc)
    _protect_need_state(doc, previous)
    _protect_status_transition(doc, previous)
    _protect_conversion_links(doc, previous)


def validate_development_action(doc):
    if not frappe.db.exists("Employee", doc.employee):
        frappe.throw(_("Employee does not exist."))
    expected = ACTION_SOURCE_DOCTYPE.get(doc.source_type)
    if expected and doc.source_doctype != expected:
        frappe.throw(_("Source Document Type must be {0} for source {1}.").format(expected, doc.source_type))
    if not frappe.db.exists(doc.source_doctype, doc.source_document):
        frappe.throw(_("Source Document does not exist."))
    if doc.target_date and getdate(doc.target_date) < getdate(today()) and doc.status in {"Draft", "Planned"}:
        frappe.throw(_("Target Date cannot be in the past for a new development action."))
    if doc.action_type == "Training" and doc.training_need_request:
        request = frappe.get_doc("Training Need Request", doc.training_need_request)
        if request.status in {"Rejected", "Cancelled"}:
            frappe.throw(_("The linked Training Need Request is not active."))
    if doc.status == "Completed":
        if not doc.completion_date:
            frappe.throw(_("Completion Date is required."))
        if doc.completion_evidence_type == "Employee Document Record" and not doc.completion_document:
            frappe.throw(_("Completion Document is required."))
        if doc.completion_evidence_type == "External URL" and not doc.completion_url:
            frappe.throw(_("Completion URL is required."))
        if not doc.completed_by:
            doc.completed_by = frappe.session.user
        if not doc.completed_on:
            doc.completed_on = now_datetime()
    if doc.status in {"Planned", "In Progress"} and not doc.planned_by:
        doc.planned_by = frappe.session.user
        doc.planned_on = now_datetime()


def _validate_need_dates(doc):
    if doc.preferred_start_date and doc.preferred_end_date and getdate(doc.preferred_end_date) < getdate(doc.preferred_start_date):
        frappe.throw(_("Preferred End Date cannot be before Preferred Start Date."))


def _validate_need_scope(doc):
    if doc.request_scope == "Individual Employee" and not doc.requested_for_employee:
        frappe.throw(_("Requested for Employee is required for an individual request."))
    if doc.request_scope == "Named Group" and not [row for row in doc.participants if row.include]:
        frappe.throw(_("At least one included participant is required."))
    required = {
        "Designation": ("designation",),
        "Department": ("department",),
        "Project Team": ("project",),
        "Criteria-based Group": (),
    }
    for fieldname in required.get(doc.request_scope, ()):
        if not doc.get(fieldname):
            frappe.throw(_("{0} is required for scope {1}.").format(doc.meta.get_label(fieldname), doc.request_scope))
    if doc.request_scope == "Criteria-based Group" and not any((doc.branch, doc.department, doc.designation, doc.employment_type, doc.employee_grade, doc.work_location, doc.project)):
        frappe.throw(_("Provide at least one employee-selection criterion."))


def _validate_need_source(doc):
    expected = SOURCE_DOCTYPE.get(doc.need_source)
    if expected:
        if doc.source_doctype != expected:
            frappe.throw(_("Source Document Type must be {0} for {1}.").format(expected, doc.need_source))
        if not doc.source_document or not frappe.db.exists(expected, doc.source_document):
            frappe.throw(_("A valid source document is required."))
    elif doc.source_document and (not doc.source_doctype or not frappe.db.exists(doc.source_doctype, doc.source_document)):
        frappe.throw(_("Source Document is invalid."))


def _validate_need_funding(doc):
    if doc.funding_required:
        if not doc.currency:
            frappe.throw(_("Currency is required when funding is required."))
        if doc.estimated_cost is not None and doc.estimated_cost < 0:
            frappe.throw(_("Estimated Cost cannot be negative."))
        if not any((doc.project, doc.cost_center, doc.funding_agreement, doc.budget_line)):
            frappe.throw(_("Provide at least one funding context: Project, Cost Center, Funding Agreement, or Budget Line."))
    if doc.project and frappe.get_meta("Project").has_field("company"):
        company = frappe.db.get_value("Project", doc.project, "company")
        if company and company != doc.company:
            frappe.throw(_("Project must belong to Company {0}.").format(doc.company))
    if doc.cost_center:
        company = frappe.db.get_value("Cost Center", doc.cost_center, "company")
        if company and company != doc.company:
            frappe.throw(_("Cost Center must belong to Company {0}.").format(doc.company))


def _validate_participants(doc):
    seen = set()
    for row in doc.participants:
        if row.employee in seen:
            frappe.throw(_("Duplicate participant: {0}.").format(row.employee))
        seen.add(row.employee)
        if row.employee:
            employee = frappe.get_doc("Employee", row.employee)
            if employee.status != "Active":
                frappe.throw(_("Participant {0} is not active.").format(row.employee))
            if employee.company and employee.company != doc.company:
                frappe.throw(_("Participant {0} belongs to another company.").format(row.employee))


def _protect_status_transition(doc, previous):
    if not previous:
        if doc.status != "Draft":
            frappe.throw(_("A new Training Need Request must start in Draft."))
        return
    if doc.status != previous.status and not doc.flags.get("qorg_status_transition"):
        frappe.throw(_("Use the lifecycle actions to change Status."))


def _protect_need_state(doc, previous):
    if not previous:
        return
    if previous.status in NEED_FINAL and doc.status != previous.status:
        frappe.throw(_("A {0} request cannot be changed.").format(previous.status))
    if previous.status not in NEED_EDITABLE:
        protected = ("training_need_title", "company", "request_scope", "need_source", "justification", "training_objectives", "expected_outcomes", "funding_required", "estimated_cost", "currency", "project", "cost_center", "funding_agreement", "budget_line")
        changed = [field for field in protected if doc.get(field) != previous.get(field)]
        if changed:
            frappe.throw(_("Return the request before changing: {0}.").format(", ".join(doc.meta.get_label(field) for field in changed)))


def _protect_conversion_links(doc, previous):
    if not previous:
        return
    for fieldname in ("training_program", "training_event", "conversion_mode", "converted_by", "converted_on", "conversion_snapshot"):
        if previous.get(fieldname) and doc.get(fieldname) != previous.get(fieldname):
            frappe.throw(_("Conversion fields are system controlled."))


def resolve_participants(doc):
    if doc.request_scope == "Individual Employee":
        return [doc.requested_for_employee]
    if doc.request_scope == "Named Group":
        return [row.employee for row in doc.participants if row.include]
    filters = {"status": "Active", "company": doc.company}
    mapping = {"branch": doc.branch, "department": doc.department, "designation": doc.designation, "employment_type": doc.employment_type, "grade": doc.employee_grade}
    for fieldname, value in mapping.items():
        if value and frappe.get_meta("Employee").has_field(fieldname):
            filters[fieldname] = value
    if doc.request_scope == "Project Team" and doc.project and frappe.get_meta("Employee").has_field("qorg_project"):
        filters["qorg_project"] = doc.project
    return frappe.get_all("Employee", filters=filters, pluck="name", order_by="name")


def transition_training_need(name, action, reason=None):
    doc = frappe.get_doc("Training Need Request", name)
    doc.check_permission("write")
    transitions = {
        "submit_for_hr_review": ({"Draft", "Returned"}, "Pending HR Review", None),
        "send_for_approval": ({"Pending HR Review"}, "Pending Approval", {"HR User", "HR Manager"}),
        "approve": ({"Pending Approval"}, "Approved", {"HR Manager"}),
        "return": ({"Pending HR Review", "Pending Approval"}, "Returned", {"HR User", "HR Manager"}),
        "reject": ({"Pending HR Review", "Pending Approval"}, "Rejected", {"HR Manager"}),
        "cancel": ({"Draft", "Returned", "Approved"}, "Cancelled", None),
    }
    if action not in transitions:
        frappe.throw(_("Unsupported action."))
    allowed, target, role = transitions[action]
    if doc.status not in allowed:
        frappe.throw(_("Action {0} is not allowed from status {1}.").format(action, doc.status))
    if role and not role.intersection(frappe.get_roles()):
        frappe.throw(_("One of these roles is required: {0}.").format(", ".join(sorted(role))), frappe.PermissionError)
    if action in {"return", "reject"} and not (reason or "").strip():
        frappe.throw(_("A reason is required."))
    doc.status = target
    if target == "Pending Approval":
        doc.hr_reviewed_by = frappe.session.user
        doc.hr_reviewed_on = now_datetime()
    elif target == "Approved":
        doc.approved_by = frappe.session.user
        doc.approved_on = now_datetime()
    if action in {"return", "reject"}:
        doc.return_or_rejection_reason = reason
    doc.flags.ignore_permissions = True
    doc.flags.qorg_status_transition = True
    doc.save()
    return {"name": doc.name, "status": doc.status}


def convert_training_need(name, mode, existing_program=None, event_values=None):
    doc = frappe.get_doc("Training Need Request", name)
    doc.check_permission("write")
    if "HR Manager" not in frappe.get_roles() and "HR User" not in frappe.get_roles():
        frappe.throw(_("HR User or HR Manager role is required."), frappe.PermissionError)
    if doc.status == "Converted":
        return {"training_program": doc.training_program, "training_event": doc.training_event, "already_converted": True}
    if doc.status != "Approved":
        frappe.throw(_("Only an Approved request can be converted."))
    if mode not in {"Link Existing Program", "Create Training Program", "Create Training Event"}:
        frappe.throw(_("Invalid conversion mode."))
    program = existing_program or doc.training_program
    created = []
    if mode == "Link Existing Program":
        if not program or not frappe.db.exists("Training Program", program):
            frappe.throw(_("A valid existing Training Program is required."))
    elif mode in {"Create Training Program", "Create Training Event"} and not program:
        program, program_created = _create_program(doc)
        if program_created:
            created.append("Training Program")
    event = None
    if mode == "Create Training Event":
        event = _create_event(doc, program, event_values or {})
        created.append("Training Event")
    snapshot = {"mode": mode, "participants": resolve_participants(doc), "created": created, "program": program, "event": event}
    frappe.db.set_value("Training Need Request", doc.name, {"status": "Converted", "conversion_mode": mode, "training_program": program, "training_event": event, "converted_by": frappe.session.user, "converted_on": now_datetime(), "conversion_snapshot": json.dumps(snapshot, ensure_ascii=False, default=str)}, update_modified=True)
    return snapshot


def _create_program(doc):
    duplicate = frappe.db.get_value("Training Program", {"training_program": doc.training_need_title, "company": doc.company}, "name")
    if duplicate:
        return duplicate, False
    program = frappe.new_doc("Training Program")
    values = {"training_program": doc.training_need_title, "company": doc.company, "description": _program_description(doc), "qorg_training_need_request": doc.name}
    _set_known(program, values)
    if program.meta.has_field("status"):
        options = (program.meta.get_field("status").options or "").splitlines()
        if "Active" in options:
            program.status = "Active"
    program.insert(ignore_permissions=True)
    return program.name, True


def _create_event(doc, program, values):
    required = ("start_time", "end_time")
    for fieldname in required:
        if not values.get(fieldname):
            frappe.throw(_("{0} is required to create a Training Event.").format(fieldname))
    if getdate(values["end_time"]) < getdate(values["start_time"]):
        frappe.throw(_("Training Event End Time cannot be before Start Time."))
    event = frappe.new_doc("Training Event")
    defaults = {"event_name": values.get("event_name") or doc.training_need_title, "training_program": program, "company": doc.company, "start_time": values["start_time"], "end_time": values["end_time"], "location": values.get("location"), "type": values.get("type"), "level": values.get("level"), "introduction": doc.training_objectives, "qorg_training_need_request": doc.name, "qorg_project": doc.project, "qorg_cost_center": doc.cost_center, "qorg_funding_agreement": doc.funding_agreement, "qorg_budget_line": doc.budget_line}
    _set_known(event, defaults)
    for employee in resolve_participants(doc):
        event.append("employees", {"employee": employee})
    event.insert(ignore_permissions=True)
    return event.name


def _set_known(target, values):
    for fieldname, value in values.items():
        if value not in (None, "") and target.meta.has_field(fieldname):
            target.set(fieldname, value)


def _program_description(doc):
    return "\n\n".join(filter(None, [doc.justification, doc.training_objectives, doc.expected_outcomes]))
