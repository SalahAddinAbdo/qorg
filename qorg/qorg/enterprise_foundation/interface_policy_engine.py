from __future__ import annotations

import hashlib
import json

import frappe
from frappe.utils import has_common, now_datetime

from qorg.qorg.enterprise_foundation.constants import CONFIGURATION_VERSION

INTERFACE_PREFIX = "Interface Policy::"
DENY_ROLE = "QOrg Disabled Component"
CUSTOM_ROLE_TYPES = {"Report": "report", "Page": "page"}
SUPPORTED_TYPES = {"Report", "Page"}


def _key(component_type: str, component_name: str) -> str:
    return f"{INTERFACE_PREFIX}{component_type}::{component_name}"


def _ensure_deny_role() -> str:
    if not frappe.db.exists("Role", DENY_ROLE):
        frappe.get_doc(
            {
                "doctype": "Role",
                "role_name": DENY_ROLE,
                "desk_access": 0,
                "disabled": 1,
            }
        ).insert(ignore_permissions=True)
    return DENY_ROLE


def _custom_role(component_type: str, component_name: str):
    fieldname = CUSTOM_ROLE_TYPES[component_type]
    name = frappe.db.get_value("Custom Role", {fieldname: component_name}, "name")
    return frappe.get_doc("Custom Role", name) if name else None


def _roles(doc) -> list[str]:
    return sorted(
        {
            row.role
            for row in (getattr(doc, "roles", None) or [])
            if getattr(row, "role", None)
        }
    )


def _snapshot(component_type: str, component_name: str) -> dict:
    custom = _custom_role(component_type, component_name)
    return {
        "custom_role_exists": bool(custom),
        "custom_roles": _roles(custom) if custom else [],
    }


def _save_state(
    component_type: str,
    component_name: str,
    visibility: str,
    snapshot: dict,
    allowed_roles: list[str],
) -> None:
    key = _key(component_type, component_name)
    state = (
        frappe.get_doc("Managed Configuration State", key)
        if frappe.db.exists("Managed Configuration State", key)
        else frappe.new_doc("Managed Configuration State")
    )
    details = {
        "component_type": component_type,
        "component_name": component_name,
        "visibility": visibility,
        "snapshot": snapshot,
        "allowed_roles": allowed_roles,
    }
    state.component_type = "Other"
    state.component_key = key
    state.managed_version = CONFIGURATION_VERSION
    state.management_status = "Managed"
    state.last_checked_on = now_datetime()
    state.last_seen_fingerprint = visibility
    state.applied_fingerprint = hashlib.sha256(
        json.dumps(details, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    state.details = json.dumps(details, sort_keys=True)
    state.flags.ignore_permissions = True
    state.save()


def _set_custom_roles(component_type: str, component_name: str, roles: list[str]) -> None:
    fieldname = CUSTOM_ROLE_TYPES[component_type]
    custom = _custom_role(component_type, component_name)
    if not custom:
        custom = frappe.new_doc("Custom Role")
        custom.set(fieldname, component_name)
    custom.set("roles", [{"role": role} for role in roles])
    custom.flags.ignore_permissions = True
    custom.save()


def _remove_custom_role(component_type: str, component_name: str) -> None:
    custom = _custom_role(component_type, component_name)
    if custom:
        frappe.delete_doc("Custom Role", custom.name, ignore_permissions=True, force=True)


def restore_interface_policy(component_type: str, component_name: str) -> str:
    key = _key(component_type, component_name)
    if frappe.db.exists("Managed Configuration State", key):
        state = frappe.get_doc("Managed Configuration State", key)
        details = frappe.parse_json(state.details) or {}
        snapshot = details.get("snapshot") or {}
        if snapshot.get("custom_role_exists"):
            _set_custom_roles(
                component_type,
                component_name,
                snapshot.get("custom_roles") or [],
            )
        else:
            _remove_custom_role(component_type, component_name)
        frappe.delete_doc(
            "Managed Configuration State",
            key,
            ignore_permissions=True,
            force=True,
        )
    frappe.clear_cache()
    return "Visible"


def apply_interface_policy(
    component_type: str,
    component_name: str,
    visibility: str,
    allowed_roles: str | None = None,
) -> str:
    if frappe.session.user != "Administrator":
        frappe.throw(
            "Only Administrator can apply interface policies.",
            frappe.PermissionError,
        )
    if component_type not in SUPPORTED_TYPES:
        frappe.throw(
            f"Policy application for {component_type} is not enabled yet."
        )
    if visibility == "Visible":
        return restore_interface_policy(component_type, component_name)

    key = _key(component_type, component_name)
    state = (
        frappe.get_doc("Managed Configuration State", key)
        if frappe.db.exists("Managed Configuration State", key)
        else None
    )
    snapshot = (
        (frappe.parse_json(state.details) or {}).get("snapshot")
        if state
        else _snapshot(component_type, component_name)
    )
    requested_roles = [
        role.strip()
        for role in (allowed_roles or "").split(",")
        if role.strip()
    ]
    for role in requested_roles:
        if not frappe.db.exists("Role", role):
            frappe.throw(f"Role {role} does not exist.")

    effective_roles = (
        requested_roles
        if visibility == "Restricted" and requested_roles
        else [_ensure_deny_role()]
    )
    _set_custom_roles(component_type, component_name, effective_roles)
    _save_state(
        component_type,
        component_name,
        visibility,
        snapshot,
        requested_roles,
    )
    frappe.clear_cache()
    return visibility


def active_interface_policies() -> dict[tuple[str, str], dict]:
    result = {}
    for row in frappe.get_all(
        "Managed Configuration State",
        filters={"component_key": ("like", f"{INTERFACE_PREFIX}%")},
        fields=["details"],
    ):
        details = frappe.parse_json(row.details) or {}
        component_type = details.get("component_type")
        component_name = details.get("component_name")
        if component_type and component_name:
            result[(component_type, component_name)] = details
    return result


def get_interface_policy(component_type: str, component_name: str) -> dict:
    return active_interface_policies().get(
        (component_type, component_name),
        {"visibility": "Visible", "allowed_roles": []},
    )


def is_interface_allowed(component_type: str, component_name: str) -> bool:
    if frappe.session.user == "Administrator":
        return True
    policy = get_interface_policy(component_type, component_name)
    visibility = policy.get("visibility", "Visible")
    if visibility in {"Disabled", "Deprecated"}:
        return False
    if visibility == "Restricted":
        allowed_roles = policy.get("allowed_roles") or []
        return bool(allowed_roles and has_common(frappe.get_roles(), allowed_roles))
    return True
