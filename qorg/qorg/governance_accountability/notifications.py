from __future__ import annotations

import hashlib,json
import frappe
from frappe import _
from frappe.utils import now_datetime

SENSITIVE={"Confidential","Highly Confidential"}
TEMPLATES={
 "Acknowledgement":"Accountability - Case Acknowledgement - Bilingual",
 "Status Update":"Accountability - Case Status Update - Bilingual",
 "Response":"Accountability - Case Response - Bilingual",
 "Closure":"Accountability - Case Closure - Bilingual",
}

def _recipient(doc):
    if doc.anonymous or not doc.consent_to_contact:return None
    return doc.email

def _safe_context(doc):
    settings=frappe.get_single("Accountability Settings")
    sensitive=bool(settings.hide_sensitive_details_in_notifications and doc.confidentiality in SENSITIVE)
    return {"doc":doc,"case_reference":doc.name,"case_status":doc.status,"subject":(_("Confidential case") if sensitive else doc.subject),"details_hidden":sensitive}

@frappe.whitelist(methods=["POST"])
def send_case_message(name,notification_type):
    doc=frappe.get_doc("Accountability Case",name)
    if not frappe.has_permission("Accountability Case","write",doc=doc):frappe.throw(_("Not permitted."),frappe.PermissionError)
    recipient=_recipient(doc)
    if not recipient:frappe.throw(_("The case has no permitted email recipient."))
    template_name=TEMPLATES.get(notification_type)
    if not template_name:frappe.throw(_("Unsupported accountability notification type."))
    template=frappe.get_doc("Email Template",template_name);context=_safe_context(doc)
    subject=frappe.render_template(template.subject,context);message=frappe.render_template(template.response_html or template.response,context)
    frappe.sendmail(recipients=[recipient],subject=subject,message=message,reference_doctype=doc.doctype,reference_name=doc.name,now=True)
    if notification_type=="Acknowledgement" and not doc.acknowledged_on:doc.acknowledged_on=now_datetime();doc.status="Acknowledged"
    if notification_type in ("Status Update","Response"):doc.last_update_to_reporter_on=now_datetime()
    doc.save();return {"sent":True,"recipient":recipient,"notification_type":notification_type}
