from __future__ import annotations

import hashlib
import secrets

import frappe
from frappe import _
from frappe.utils import add_days, now_datetime

from qorg.qorg.governance_accountability.security import enforce_rate_limit, validate_captcha

PUBLIC_STATUSES={"Received","Acknowledged","Triaged","Assigned","Under Review","Referred","Under Investigation","Action in Progress","Response Prepared","Response Delivered","Pending Confirmation","Closed","Escalated","Appealed","Reopened","Withdrawn","Out of Scope","Referred Externally","Unable to Contact"}

def _hash(token): return hashlib.sha256((token or "").encode()).hexdigest()

def _enabled_value(doctype,name,field='enabled'):
    return bool(frappe.db.get_value(doctype,name,field))

@frappe.whitelist(allow_guest=True,methods=["POST"])
def submit_accountability_case(case_type,category,channel,subject,case_details,company,anonymous=0,stakeholder_type=None,reporter_name=None,email=None,mobile_no=None,project=None,location_details=None,consent_to_contact=0,captcha_token=None):
    settings=frappe.get_single("Governance and Accountability Settings")
    if not settings.enable_public_intake: frappe.throw(_("Public accountability intake is not enabled."),frappe.PermissionError)
    enforce_rate_limit("intake",settings.intake_rate_limit_per_hour)
    validate_captcha(captcha_token)
    anonymous=int(anonymous or 0)
    if anonymous and not settings.allow_anonymous_cases: frappe.throw(_("Anonymous submissions are disabled."))
    for dt,name in (("Accountability Case Type",case_type),("Accountability Category",category),("Accountability Channel",channel)):
        if not name or not _enabled_value(dt,name): frappe.throw(_("The selected intake classification is unavailable."))
    if frappe.db.get_value("Accountability Category",category,"sensitive_category"):
        # Never disclose routing or sensitive handling to a public submitter.
        pass
    if not anonymous and not reporter_name: frappe.throw(_("Reporter Name is required unless the submission is anonymous."))
    token=secrets.token_urlsafe(32)
    doc=frappe.get_doc({
      "doctype":"Accountability Case","case_type":case_type,"category":category,"channel":channel,
      "received_on":now_datetime(),"status":"Received","company":company,"project":project,
      "anonymous":anonymous,"stakeholder_type":"Anonymous" if anonymous else (stakeholder_type or "Other"),
      "reporter_name":None if anonymous else reporter_name,"email":None if anonymous else email,
      "mobile_no":None if anonymous else mobile_no,"consent_to_contact":0 if anonymous else int(consent_to_contact or 0),
      "subject":subject,"case_details":case_details,"location_details":location_details,
      "external_tracking_enabled":1,"external_tracking_key_hash":_hash(token),"external_tracking_created_on":now_datetime(),
    })
    doc.flags.ignore_permissions=True
    doc.insert(ignore_permissions=True)
    return {"case_reference":doc.name,"tracking_token":token,"status":"Received"}

@frappe.whitelist(allow_guest=True,methods=["POST"])
def track_accountability_case(case_reference,tracking_token,captcha_token=None):
    settings=frappe.get_single("Governance and Accountability Settings")
    if not settings.enable_public_tracking: frappe.throw(_("Public accountability tracking is not enabled."),frappe.PermissionError)
    enforce_rate_limit("tracking",settings.tracking_rate_limit_per_hour)
    validate_captcha(captcha_token)
    if not case_reference or not tracking_token: frappe.throw(_("Case reference and tracking token are required."))
    doc=frappe.get_doc("Accountability Case",case_reference)
    token_created_on=doc.external_tracking_created_on or doc.creation
    if token_created_on and settings.tracking_token_validity_days and now_datetime() > add_days(token_created_on,int(settings.tracking_token_validity_days)):
        frappe.throw(_("This tracking token has expired."),frappe.PermissionError)
    if doc.closed_on and settings.disable_tracking_after_closure_days and now_datetime() > add_days(doc.closed_on,int(settings.disable_tracking_after_closure_days)):
        frappe.throw(_("External tracking is no longer available for this closed case."),frappe.PermissionError)
    if not doc.external_tracking_enabled or not secrets.compare_digest(doc.external_tracking_key_hash or "",_hash(tracking_token)):
        frappe.throw(_("Invalid case reference or tracking token."),frappe.PermissionError)
    frappe.db.set_value("Accountability Case",doc.name,"external_tracking_last_accessed",now_datetime(),update_modified=False)
    status=doc.status if doc.status in PUBLIC_STATUSES else "Under Review"
    responses=[]
    for row in doc.response_logs or []:
        if row.response_delivered:responses.append({"response_on":row.response_on,"response_summary":row.response_summary})
    return {"case_reference":doc.name,"status":status,"received_on":doc.received_on,"last_update":doc.last_update_to_reporter_on,"responses":responses[-3:]}
