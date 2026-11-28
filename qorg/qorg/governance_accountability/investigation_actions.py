from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import now_datetime

MANAGERS = {"System Manager", "Accountability Manager", "Compliance Manager"}


def _manager_required():
    if frappe.session.user != "Administrator" and not MANAGERS.intersection(frappe.get_roles()):
        frappe.throw(_("A governance manager role is required."), frappe.PermissionError)


def _doc(doctype, name):
    doc = frappe.get_doc(doctype, name)
    if not frappe.has_permission(doctype, "write", doc=doc):
        frappe.throw(_("Not permitted."), frappe.PermissionError)
    return doc


@frappe.whitelist(methods=["POST"])
def create_investigation(accountability_case, subject, allegation_summary, scope, objectives, lead_investigator=None, target_completion_date=None):
    _manager_required()
    case = frappe.get_doc("Accountability Case", accountability_case)
    if case.status in ("Closed", "Withdrawn", "Duplicate", "Out of Scope"):
        frappe.throw(_("An inactive accountability case cannot open an investigation."))
    existing = frappe.db.get_value("Investigation Case", {"accountability_case": accountability_case, "status": ["not in", ["Closed", "Cancelled"]]})
    if existing:
        frappe.throw(_("An active Investigation Case already exists: {0}").format(existing))
    doc = frappe.get_doc({
        "doctype":"Investigation Case", "subject":subject, "accountability_case":accountability_case,
        "company":case.company, "project":case.project, "confidentiality":"Highly Confidential" if case.confidentiality=="Highly Confidential" else "Confidential",
        "allegation_summary":allegation_summary, "scope":scope, "objectives":objectives,
        "lead_investigator":lead_investigator, "target_completion_date":target_completion_date,
    })
    if lead_investigator:
        doc.append("team_members", {"user":lead_investigator,"role_in_investigation":"Lead Investigator","appointed_on":frappe.utils.today()})
    doc.insert()
    case.status = "Under Investigation"; case.investigation_required = 1; case.save()
    return doc.name


@frappe.whitelist(methods=["POST"])
def authorize_investigation(name):
    _manager_required(); doc=_doc("Investigation Case",name)
    if doc.status != "Draft": frappe.throw(_("Only a draft investigation can be authorized."))
    doc.status="Authorized"; doc.authorized_on=now_datetime(); doc.authorized_by=frappe.session.user
    doc.conflict_reviewed_by=frappe.session.user; doc.conflict_reviewed_on=now_datetime(); doc.save(); return doc.name


@frappe.whitelist(methods=["POST"])
def move_investigation(name, target_status):
    doc=_doc("Investigation Case",name)
    allowed={"Authorized":"Planning","Planning":"Evidence Collection","Evidence Collection":"Interviews","Interviews":"Analysis","Analysis":"Report Review"}
    if allowed.get(doc.status)!=target_status: frappe.throw(_("Invalid investigation stage transition."))
    doc.status=target_status; doc.save(); return doc.name


@frappe.whitelist(methods=["POST"])
def close_investigation(name, closure_notes):
    _manager_required(); doc=_doc("Investigation Case",name)
    if doc.status != "Report Review": frappe.throw(_("Investigation must be in Report Review before closure."))
    doc.status="Closed"; doc.report_approved_by=frappe.session.user; doc.report_approved_on=now_datetime(); doc.closed_on=now_datetime(); doc.closed_by=frappe.session.user; doc.closure_notes=closure_notes; doc.save()
    case=frappe.get_doc("Accountability Case",doc.accountability_case); case.status="Action in Progress" if frappe.db.exists("Corrective Action", {"accountability_case":case.name,"status":["not in",["Closed","Cancelled"]]}) else "Under Review"; case.save()
    return doc.name


@frappe.whitelist(methods=["POST"])
def approve_corrective_action(name):
    _manager_required(); doc=_doc("Corrective Action",name)
    if doc.status!="Draft": frappe.throw(_("Only a draft Corrective Action can be approved."))
    doc.status="Approved"; doc.approved_by=frappe.session.user; doc.approved_on=now_datetime(); doc.save(); return doc.name


@frappe.whitelist(methods=["POST"])
def add_corrective_update(name, progress_percent, status, update_summary, evidence=None, next_step=None):
    doc=_doc("Corrective Action",name)
    if doc.status in ("Closed","Cancelled"): frappe.throw(_("Closed actions cannot be updated."))
    value=float(progress_percent or 0)
    if value<0 or value>100: frappe.throw(_("Progress Percent must be between 0 and 100."))
    doc.append("updates", {"update_on":now_datetime(),"updated_by":frappe.session.user,"progress_percent":value,"status":status,"update_summary":update_summary,"evidence":evidence,"next_step":next_step})
    doc.status="Pending Verification" if status=="Completed" else "In Progress"; doc.save(); return doc.name


@frappe.whitelist(methods=["POST"])
def verify_corrective_action(name, result, verification_method, verification_notes=None, verification_evidence=None):
    _manager_required(); doc=_doc("Corrective Action",name)
    if doc.status!="Pending Verification": frappe.throw(_("Corrective Action must be Pending Verification."))
    if result not in ("Effective","Partially Effective","Ineffective"): frappe.throw(_("Invalid effectiveness result."))
    doc.effectiveness_result=result; doc.verification_method=verification_method; doc.verification_notes=verification_notes; doc.verification_evidence=verification_evidence; doc.verified_by=frappe.session.user; doc.verified_on=now_datetime(); doc.status="Verified Effective" if result=="Effective" else "Verified Ineffective"; doc.save(); return doc.name


@frappe.whitelist(methods=["POST"])
def close_corrective_action(name, closure_notes):
    _manager_required(); doc=_doc("Corrective Action",name)
    if doc.status!="Verified Effective": frappe.throw(_("Only a verified effective action can be closed."))
    doc.status="Closed"; doc.closed_on=now_datetime(); doc.closed_by=frappe.session.user; doc.closure_notes=closure_notes; doc.save(); return doc.name

@frappe.whitelist(methods=["POST"])
def reopen_corrective_action(name,reason):
    _manager_required();old=_doc("Corrective Action",name)
    if old.status!="Closed":frappe.throw(_("Only a closed Corrective Action can be reopened."))
    new=frappe.copy_doc(old);new.reopened_from=old.name;new.status="Draft";new.closed_on=None;new.closed_by=None;new.verified_on=None;new.verified_by=None;new.effectiveness_result=None;new.closure_notes="Reopened: "+reason;new.insert();return new.name
