from __future__ import annotations

import frappe


def is_administrator(user: str | None = None) -> bool:
    return (user or frappe.session.user) == "Administrator"


def require_administrator() -> None:
    if not is_administrator():
        frappe.throw("Only Administrator can use Feature Control Center.", frappe.PermissionError)


def feature_control_center_has_permission(doc=None, user=None, permission_type=None):
    return is_administrator(user)


def managed_state_has_permission(doc=None, user=None, permission_type=None):
    return is_administrator(user)
