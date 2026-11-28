from __future__ import annotations

import frappe
from frappe import _


def protect_procurement_complaint(doc, method=None):
    if not frappe.db.exists("DocType", "Accountability Settings"):
        return
    settings = frappe.get_single("Accountability Settings")
    if not settings.lock_legacy_procurement_complaints:
        return
    if doc.is_new():
        frappe.throw(_("Create a new Accountability Case instead of a Procurement Complaint."))
    migrated = frappe.db.exists("Accountability Case", {"legacy_doctype": "Procurement Complaint", "legacy_name": doc.name})
    if migrated and not getattr(doc.flags, "qorg_allow_legacy_update", False):
        frappe.throw(_("This legacy Procurement Complaint is read only. Open the linked Accountability Case {0}.").format(migrated))
