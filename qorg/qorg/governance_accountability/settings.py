from __future__ import annotations

import frappe


def get_settings():
    if not frappe.db.exists("DocType", "Governance and Accountability Settings"):
        frappe.throw("Governance and Accountability Settings is not installed.")
    return frappe.get_single("Governance and Accountability Settings")
