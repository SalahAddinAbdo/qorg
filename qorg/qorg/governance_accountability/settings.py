from __future__ import annotations

import frappe


def get_settings():
    if not frappe.db.exists("DocType", "Accountability Settings"):
        frappe.throw("Accountability Settings is not installed.")
    return frappe.get_single("Accountability Settings")
