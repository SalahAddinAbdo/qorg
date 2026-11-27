from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import get_datetime, now_datetime

from qorg.qorg.people_and_opportunities.portal_ownership import is_website_user, portal_owned_reference

ALLOWED_REFERENCE_DOCTYPES = {"Participation Application", "Job Applicant"}


def _reference(doc):
    doctype = doc.get("reference_doctype") or doc.get("link_doctype")
    name = doc.get("reference_docname") or doc.get("link_name")
    return doctype, name


def validate_web_form_request(doc, method=None):
    if not is_website_user():
        return
    old = doc.get_doc_before_save()
    if old:
        for fieldname in ("owner", "reference_doctype", "reference_docname", "link_doctype", "link_name"):
            if doc.meta.has_field(fieldname) and doc.get(fieldname) != old.get(fieldname):
                frappe.throw(_("The Web Form Request reference cannot be changed."), frappe.PermissionError)
    doctype, name = _reference(doc)
    if doctype and doctype not in ALLOWED_REFERENCE_DOCTYPES:
        frappe.throw(_("This document type is not allowed for an external Web Form Request."), frappe.PermissionError)
    if doctype and name and not portal_owned_reference(doctype, name):
        frappe.throw(_("The referenced record is not owned by the current user."), frappe.PermissionError)
    if doc.meta.has_field("expires_on") and doc.get("expires_on"):
        if get_datetime(doc.expires_on) <= now_datetime():
            frappe.throw(_("The Web Form Request has expired."), frappe.PermissionError)
