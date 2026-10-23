from __future__ import annotations

import frappe

READ_ONLY_POLICIES = {"Read Only", "Feature Disabled", "Deprecated"}
BLOCKED_POLICIES = {"Restricted"}


def get_model_policy(doctype: str | None) -> str:
    if not doctype or not frappe.db.exists("DocType", "Feature Control Center"):
        return "Enabled"
    try:
        value = frappe.db.get_value(
            "Model Control Entry",
            {
                "parent": "Feature Control Center",
                "parenttype": "Feature Control Center",
                "parentfield": "models",
                "document_type": doctype,
            },
            "current_policy",
        )
        return value or "Enabled"
    except Exception:
        return "Enabled"


def enforce_model_policy(doc, method=None):
    if frappe.session.user == "Administrator":
        return
    if getattr(frappe.flags, "in_install", False) or getattr(frappe.flags, "in_migrate", False):
        return
    policy = get_model_policy(getattr(doc, "doctype", None))
    if policy in READ_ONLY_POLICIES:
        frappe.throw(
            f"{doc.doctype} is currently {policy} and cannot be changed.",
            frappe.PermissionError,
        )
    if policy in BLOCKED_POLICIES:
        frappe.throw(
            f"Access to {doc.doctype} is currently restricted.",
            frappe.PermissionError,
        )
