from __future__ import annotations

import frappe

from qorg.qorg.enterprise_foundation.model_policy_engine import active_native_policies

CONTROL_DOCTYPES = {
    "Feature Control Center",
    "Model Control Entry",
    "Configuration Audit Result",
    "Managed Configuration State",
}
PROTECTED_POLICIES = {"Read Only", "Restricted", "Feature Disabled", "Deprecated"}


def get_model_policy(doctype: str | None) -> str:
    if not doctype:
        return "Enabled"
    return active_native_policies().get(doctype, "Enabled")


def get_policy_map() -> dict[str, str]:
    return active_native_policies()


def _bypass(doc) -> bool:
    return bool(
        frappe.session.user == "Administrator"
        or getattr(doc, "doctype", None) in CONTROL_DOCTYPES
        or getattr(frappe.flags, "in_install", False)
        or getattr(frappe.flags, "in_migrate", False)
        or getattr(frappe.flags, "qorg_policy_bypass", False)
    )


def enforce_model_policy(doc, method=None):
    if _bypass(doc):
        return
    policy = get_model_policy(getattr(doc, "doctype", None))
    if policy in PROTECTED_POLICIES:
        frappe.throw(
            f"{doc.doctype} is currently {policy} and cannot be changed.",
            frappe.PermissionError,
        )


def enforce_rename_policy(doctype: str):
    if frappe.session.user == "Administrator":
        return
    policy = get_model_policy(doctype)
    if policy in PROTECTED_POLICIES:
        frappe.throw(
            f"{doctype} is currently {policy} and cannot be renamed or merged.",
            frappe.PermissionError,
        )
