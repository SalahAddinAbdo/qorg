from __future__ import annotations

import frappe

DOCTYPE = "Cost Distribution Profile"
MANAGER_ROLES = ("Accounts Manager", "Projects Manager")

def repair_profile_submit_permissions():
    if not frappe.db.exists("DocType", DOCTYPE):
        return
    doc = frappe.get_doc("DocType", DOCTYPE)
    changed = False
    for row in doc.permissions:
        if row.role in MANAGER_ROLES:
            for field in ("submit", "cancel", "amend"):
                if not row.get(field):
                    row.set(field, 1)
                    changed = True
    if changed:
        doc.flags.ignore_permissions = True
        doc.save()
    frappe.clear_cache(doctype=DOCTYPE)
