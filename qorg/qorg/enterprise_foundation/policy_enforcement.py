from __future__ import annotations

import frappe

READ_ONLY_POLICIES = {"Read Only", "Feature Disabled", "Deprecated"}
RESTRICTED_POLICIES = {"Restricted"}
CONTROL_DOCTYPES = {
    "Feature Control Center",
    "Model Control Entry",
    "Configuration Audit Result",
    "Managed Configuration State",
}


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


def get_policy_map() -> dict[str, str]:
    if not frappe.db.exists("DocType", "Feature Control Center"):
        return {}
    rows = frappe.get_all(
        "Model Control Entry",
        filters={
            "parent": "Feature Control Center",
            "parenttype": "Feature Control Center",
            "parentfield": "models",
            "current_policy": ("!=", "Enabled"),
        },
        fields=["document_type", "current_policy"],
    )
    return {row.document_type: row.current_policy for row in rows if row.document_type}


def _bypass(doc) -> bool:
    doctype = getattr(doc, "doctype", None)
    return bool(
        frappe.session.user == "Administrator"
        or doctype in CONTROL_DOCTYPES
        or getattr(frappe.flags, "in_install", False)
        or getattr(frappe.flags, "in_migrate", False)
        or getattr(frappe.flags, "qorg_policy_bypass", False)
    )


def enforce_model_policy(doc, method=None):
    if _bypass(doc):
        return
    policy = get_model_policy(getattr(doc, "doctype", None))
    if policy in READ_ONLY_POLICIES:
        frappe.throw(
            f"{doc.doctype} is currently {policy} and cannot be changed.",
            frappe.PermissionError,
        )
    if policy in RESTRICTED_POLICIES:
        frappe.throw(
            f"Access to {doc.doctype} is currently restricted.",
            frappe.PermissionError,
        )


def enforce_rename_policy(doctype: str):
    if frappe.session.user == "Administrator":
        return
    policy = get_model_policy(doctype)
    if policy in READ_ONLY_POLICIES | RESTRICTED_POLICIES:
        frappe.throw(
            f"{doctype} is currently {policy} and cannot be renamed or merged.",
            frappe.PermissionError,
        )
