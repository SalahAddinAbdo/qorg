from __future__ import annotations

import frappe
from frappe import _

from qorg.qorg.people_and_opportunities.portal_ownership import is_website_user, portal_owned_reference

PROTECTED_DOCTYPES = {"External Person", "Participation Application", "Job Applicant"}


def has_file_permission(file_doc, user=None):
    user = user or frappe.session.user
    doctype = getattr(file_doc, "attached_to_doctype", None)
    name = getattr(file_doc, "attached_to_name", None)
    if doctype not in PROTECTED_DOCTYPES or not name:
        return None
    if user == "Administrator":
        return True
    if is_website_user(user):
        return portal_owned_reference(doctype, name, user=user)
    return None


def validate_sensitive_file(doc, method=None):
    doctype = doc.get("attached_to_doctype")
    name = doc.get("attached_to_name")
    if doctype not in PROTECTED_DOCTYPES or not name:
        return
    doc.is_private = 1
    old = doc.get_doc_before_save()
    if old and (old.attached_to_doctype, old.attached_to_name) != (doctype, name):
        if is_website_user():
            frappe.throw(_("Portal users cannot move an attached file to another record."), frappe.PermissionError)
        for check_doctype, check_name in (
            (old.attached_to_doctype, old.attached_to_name),
            (doctype, name),
        ):
            if check_doctype and check_name and not frappe.has_permission(check_doctype, "write", check_name):
                frappe.throw(_("Write permission is required on both records to move an attached file."), frappe.PermissionError)
