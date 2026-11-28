from __future__ import annotations


import frappe
from frappe import _
from frappe.utils import getdate, now_datetime
from qorg.qorg.governance_accountability.private_files import content_hash

PRIVILEGED = {"System Manager", "Accountability Manager", "Compliance Manager"}
CLOSED = {"Closed", "Cancelled"}


def validate_investigation(doc):
    case = frappe.get_doc("Accountability Case", doc.accountability_case)
    if case.company != doc.company:
        frappe.throw(_("Investigation Company must match the linked Accountability Case."))
    if doc.project and case.project and doc.project != case.project:
        frappe.throw(_("Investigation Project must match the linked Accountability Case."))
    if doc.lead_investigator and not frappe.db.exists("User", {"name": doc.lead_investigator, "enabled": 1}):
        frappe.throw(_("Lead Investigator must be an enabled user."))
    _validate_team(doc)
    _validate_interviews(doc)
    _validate_evidence(doc)
    _validate_transition(doc)


def _validate_team(doc):
    active = [row for row in doc.team_members or [] if not row.access_revoked]
    users = [row.user for row in active]
    if len(users) != len(set(users)):
        frappe.throw(_("An active investigation team member cannot be listed more than once."))
    leads = [row for row in active if row.role_in_investigation == "Lead Investigator"]
    if doc.status not in ("Draft", "Cancelled"):
        if len(leads) != 1:
            frappe.throw(_("Exactly one active Lead Investigator is required."))
        if doc.lead_investigator != leads[0].user:
            frappe.throw(_("Lead Investigator must match the active lead team member."))
        if not doc.independence_confirmed:
            frappe.throw(_("Investigator independence must be confirmed before authorization."))
        conflicts = [row.user for row in active if row.conflict_declared and not row.conflict_cleared_by]
        if conflicts:
            frappe.throw(_("Unresolved investigator conflicts: {0}").format(", ".join(conflicts)))


def _validate_interviews(doc):
    for row in doc.interviews or []:
        if row.interviewee_reference and not row.interviewee_reference_doctype:
            frappe.throw(_("Interviewee Reference Type is required."))
        if row.interviewee_reference and not frappe.db.exists(row.interviewee_reference_doctype, row.interviewee_reference):
            frappe.throw(_("Interviewee Reference does not exist."))
        if row.status == "Completed" and (not row.conducted_on or not row.conducted_by or not row.summary):
            frappe.throw(_("Completed interviews require date, interviewer, and summary."))


def _validate_evidence(doc):
    refs = [row.evidence_reference for row in doc.evidence_items or []]
    if len(refs) != len(set(refs)):
        frappe.throw(_("Evidence Reference must be unique within the investigation."))
    for row in doc.evidence_items or []:
        if row.file and not row.integrity_hash:
            row.integrity_hash = content_hash(row.file)
        if row.file and not row.chain_of_custody_notes:
            frappe.throw(_("Chain of Custody Notes are required for attached evidence."))


def _validate_transition(doc):
    old = doc.get_doc_before_save()
    if not old:
        return
    if old.status in CLOSED and doc.status != old.status:
        frappe.throw(_("Closed or cancelled investigations cannot be edited through direct status changes."))
    if doc.status == "Closed":
        if not doc.findings or not doc.conclusion or not doc.final_report:
            frappe.throw(_("Findings, Conclusion, and Final Report are required before closing."))
        if any(row.outcome in (None, "") for row in doc.findings):
            frappe.throw(_("Every finding requires an outcome before closure."))


def investigation_query(user=None):
    user = user or frappe.session.user
    if user == "Administrator" or PRIVILEGED.intersection(frappe.get_roles(user)):
        return ""
    escaped = frappe.db.escape(user)
    return (
        "(`tabInvestigation Case`.`lead_investigator`={user} or exists "
        "(select 1 from `tabInvestigation Team Member` tm where tm.parent=`tabInvestigation Case`.name "
        "and tm.parenttype='Investigation Case' and tm.user={user} and ifnull(tm.access_revoked,0)=0))"
    ).format(user=escaped)


def investigation_permission(doc, user=None, permission_type=None):
    user = user or frappe.session.user
    if user == "Administrator" or PRIVILEGED.intersection(frappe.get_roles(user)):
        return True
    if doc.lead_investigator == user:
        return True
    return any(row.user == user and not row.access_revoked for row in doc.team_members or [])



def _validate_source_context(doc):
    source=frappe.get_doc(doc.source_doctype,doc.source_name)
    if source.meta.has_field("company") and source.company and source.company!=doc.company:
        frappe.throw(_("Corrective Action Company must match the source document."))
    if source.meta.has_field("project") and source.project and doc.project and source.project!=doc.project:
        frappe.throw(_("Corrective Action Project must match the source document."))
    if doc.accountability_case and doc.source_doctype=="Accountability Case" and doc.accountability_case!=doc.source_name:
        frappe.throw(_("Accountability Case must match the source document."))
    if doc.investigation_case and doc.source_doctype=="Investigation Case" and doc.investigation_case!=doc.source_name:
        frappe.throw(_("Investigation Case must match the source document."))

def validate_corrective_action(doc):
    if not frappe.db.exists(doc.source_doctype, doc.source_name):
        frappe.throw(_("Source Document does not exist."))
    _validate_source_context(doc)
    if doc.responsible_user and not frappe.db.exists("User", {"name": doc.responsible_user, "enabled": 1}):
        frappe.throw(_("Responsible User must be enabled."))
    if doc.due_date and getdate(doc.due_date) < getdate(doc.creation or now_datetime()) and doc.status == "Draft":
        frappe.throw(_("Due Date cannot precede creation date."))
    old = doc.get_doc_before_save()
    if old and old.status == "Closed" and doc.status != "Closed":
        frappe.throw(_("Use the reopen action to reopen a closed Corrective Action."))
    if doc.status in ("Pending Verification", "Verified Effective", "Verified Ineffective", "Closed"):
        if not doc.updates or not any(row.status == "Completed" for row in doc.updates):
            frappe.throw(_("A completed progress update is required before verification."))
    if doc.status in ("Verified Effective", "Verified Ineffective", "Closed"):
        if not doc.verification_method or not doc.effectiveness_result or not doc.verified_by:
            frappe.throw(_("Verification Method, Effectiveness Result, and Verified By are required."))
    if doc.status == "Closed" and doc.effectiveness_result != "Effective":
        frappe.throw(_("Only an effective Corrective Action can be closed."))
