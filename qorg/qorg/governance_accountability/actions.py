from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import now_datetime

from qorg.qorg.governance_accountability.routing import apply_routing, _validate_responsible

MANAGER_ROLES = {"System Manager", "Accountability Manager"}


def _get_case(name, permission="write"):
    doc = frappe.get_doc("Accountability Case", name)
    if not frappe.has_permission("Accountability Case", permission, doc=doc):
        frappe.throw(_("Not permitted to perform this accountability action."), frappe.PermissionError)
    return doc


def _save_action(doc):
    doc.flags.ignore_validate_update_after_submit = True
    doc.save()
    return doc.name


@frappe.whitelist(methods=["POST"])
def acknowledge_case(name):
    doc = _get_case(name)
    if doc.status != "Received":
        frappe.throw(_("Only a received case can be acknowledged."))
    doc.status = "Acknowledged"
    doc.acknowledged_on = now_datetime()
    return _save_action(doc)


@frappe.whitelist(methods=["POST"])
def triage_case(name):
    doc = _get_case(name)
    if doc.status not in ("Received", "Acknowledged"):
        frappe.throw(_("Only a received or acknowledged case can be triaged."))
    if not doc.triage_outcome:
        frappe.throw(_("Triage Outcome is required."))
    if doc.triage_outcome == "In Scope":
        rule = apply_routing(doc, require_match=True)
        doc.status = "Assigned" if doc.custom_current_responsible_user else "Triaged"
        if rule and not doc.receiving_role:
            frappe.throw(_("The routing rule must define a Receiving Role."))
    elif doc.triage_outcome == "Out of Scope":
        doc.status = "Out of Scope"
    elif doc.triage_outcome == "External Referral":
        doc.status = "Referred Externally"
    elif doc.triage_outcome == "Duplicate":
        doc.status = "Duplicate"
    else:
        doc.status = "Under Review"
    return _save_action(doc)


@frappe.whitelist(methods=["POST"])
def assign_case(name, responsible_user, referral_reason, due_date=None):
    doc = _get_case(name)
    if doc.status in ("Closed", "Withdrawn", "Duplicate", "Out of Scope"):
        frappe.throw(_("A closed or inactive case cannot be assigned."))
    _validate_responsible(responsible_user, doc.receiving_role)
    previous = doc.custom_current_responsible_user
    doc.custom_previous_responsible_user = previous
    doc.custom_current_responsible_user = responsible_user
    doc.status = "Assigned"
    doc.append("referrals", {
        "from_user": frappe.session.user,
        "from_department": doc.receiving_department,
        "to_user": responsible_user,
        "to_department": doc.receiving_department,
        "to_role": doc.receiving_role,
        "referred_on": now_datetime(),
        "due_date": due_date,
        "status": "Accepted" if responsible_user == frappe.session.user else "Pending",
        "accepted_on": now_datetime() if responsible_user == frappe.session.user else None,
        "referral_reason": referral_reason,
    })
    doc.flags.qorg_atomic_workflow_handoff = True
    return _save_action(doc)


@frappe.whitelist(methods=["POST"])
def accept_referral(name):
    doc = _get_case(name)
    if doc.custom_current_responsible_user != frappe.session.user:
        frappe.throw(_("Only the current responsible user can accept the referral."), frappe.PermissionError)
    pending = next((row for row in reversed(doc.referrals or []) if row.status == "Pending" and row.to_user == frappe.session.user), None)
    if not pending:
        frappe.throw(_("No pending referral is available for this user."))
    pending.status = "Accepted"
    pending.accepted_on = now_datetime()
    doc.status = "Under Review"
    return _save_action(doc)


@frappe.whitelist(methods=["POST"])
def return_referral(name, reason):
    doc = _get_case(name)
    if doc.custom_current_responsible_user != frappe.session.user:
        frappe.throw(_("Only the current responsible user can return the referral."), frappe.PermissionError)
    active = next((row for row in reversed(doc.referrals or []) if row.status in ("Pending", "Accepted") and row.to_user == frappe.session.user), None)
    if not active:
        frappe.throw(_("No active referral is available."))
    active.status = "Returned"; active.returned_on = now_datetime(); active.return_reason = reason
    doc.custom_current_responsible_user = doc.custom_previous_responsible_user
    doc.custom_previous_responsible_user = frappe.session.user
    doc.status = "Referred"
    doc.flags.qorg_atomic_workflow_handoff = True
    return _save_action(doc)


@frappe.whitelist(methods=["POST"])
def add_follow_up(name, method, summary, next_follow_up_on=None, contact_successful=0):
    doc = _get_case(name)
    doc.append("follow_ups", {
        "follow_up_on": now_datetime(), "follow_up_by": frappe.session.user,
        "method": method, "summary": summary, "next_follow_up_on": next_follow_up_on,
        "contact_successful": int(contact_successful or 0),
    })
    doc.last_update_to_reporter_on = now_datetime() if int(contact_successful or 0) else doc.last_update_to_reporter_on
    return _save_action(doc)


@frappe.whitelist(methods=["POST"])
def add_response(name, response_method, response_summary, delivered=1, satisfaction=None):
    doc = _get_case(name)
    if frappe.db.get_value("Accountability Case Type", doc.case_type, "requires_response") and not response_summary:
        frappe.throw(_("Response Summary is required."))
    doc.append("response_logs", {
        "response_on": now_datetime(), "response_by": frappe.session.user,
        "response_method": response_method, "response_summary": response_summary,
        "response_delivered": int(delivered or 0), "satisfaction": satisfaction,
    })
    doc.status = "Response Delivered" if int(delivered or 0) else "Response Prepared"
    if int(delivered or 0):
        doc.last_update_to_reporter_on=now_datetime()
        settings=frappe.get_single("Governance and Accountability Settings")
        days=frappe.db.get_value("Accountability Case Type",doc.case_type,"update_frequency_days") or settings.update_frequency_days
        doc.next_reporter_update_due_on=frappe.utils.add_days(doc.last_update_to_reporter_on,int(days))
    return _save_action(doc)


@frappe.whitelist(methods=["POST"])
def close_case(name, closure_rationale):
    doc = _get_case(name)
    if not doc.resolution_decision:
        frappe.throw(_("Resolution Decision is required before closing."))
    doc.closure_rationale = closure_rationale
    doc.status = "Closed"
    if MANAGER_ROLES.intersection(frappe.get_roles()) or frappe.session.user == "Administrator":
        doc.closure_approved_by = frappe.session.user
    elif frappe.db.get_value("Accountability Case Type", doc.case_type, "closure_approval_required"):
        frappe.throw(_("Accountability Manager approval is required for closure."), frappe.PermissionError)
    return _save_action(doc)


@frappe.whitelist(methods=["POST"])
def reopen_case(name, reason):
    doc = _get_case(name)
    if doc.status != "Closed":
        frappe.throw(_("Only a closed case can be reopened."))
    if not (MANAGER_ROLES.intersection(frappe.get_roles()) or frappe.session.user == "Administrator"):
        frappe.throw(_("Accountability Manager role is required to reopen a case."), frappe.PermissionError)
    doc.status = "Reopened"
    doc.closure_rationale = (doc.closure_rationale or "") + "\nReopened: " + reason
    doc.closed_on = None; doc.closed_by = None; doc.closure_approved_by = None
    return _save_action(doc)
