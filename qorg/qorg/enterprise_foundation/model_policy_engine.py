from __future__ import annotations

import hashlib
import json

import frappe
from frappe.permissions import get_rights
from frappe.utils import now_datetime

from qorg.qorg.enterprise_foundation.constants import CONFIGURATION_VERSION

SNAPSHOT_PREFIX = "Model Policy::"
WRITE_RIGHTS = {
    "write", "create", "delete", "submit", "cancel", "amend", "import", "share"
}
ALL_RIGHTS = {
    "select", "read", "write", "create", "delete", "submit", "cancel", "amend",
    "print", "email", "report", "import", "export", "share",
}
READ_ONLY_POLICIES = {"Read Only", "Feature Disabled", "Deprecated"}


def _state_key(doctype: str) -> str:
    return f"{SNAPSHOT_PREFIX}{doctype}"


def _row_payload(row) -> dict:
    rights = set(get_rights(row.parent)) | ALL_RIGHTS
    payload = {
        "role": row.role,
        "permlevel": int(row.permlevel or 0),
        "if_owner": int(row.if_owner or 0),
    }
    for right in rights:
        if hasattr(row, right):
            payload[right] = int(getattr(row, right) or 0)
    return payload


def _snapshot(doctype: str) -> dict:
    custom = frappe.get_all(
        "Custom DocPerm",
        filters={"parent": doctype},
        fields=["name"],
        order_by="idx asc, permlevel asc, role asc",
    )
    if custom:
        rows = [_row_payload(frappe.get_doc("Custom DocPerm", item.name)) for item in custom]
        return {"source": "Custom DocPerm", "rows": rows}

    standard = frappe.get_all(
        "DocPerm",
        filters={"parent": doctype},
        fields=["name"],
        order_by="idx asc, permlevel asc, role asc",
    )
    rows = [_row_payload(frappe.get_doc("DocPerm", item.name)) for item in standard]
    return {"source": "DocPerm", "rows": rows}


def _fingerprint(value: dict) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


def _load_state(doctype: str):
    key = _state_key(doctype)
    if not frappe.db.exists("Managed Configuration State", key):
        return None
    return frappe.get_doc("Managed Configuration State", key)


def _save_state(doctype: str, snapshot: dict, policy: str) -> None:
    key = _state_key(doctype)
    doc = _load_state(doctype) or frappe.new_doc("Managed Configuration State")
    doc.component_type = "Other"
    doc.component_key = key
    doc.managed_version = CONFIGURATION_VERSION
    doc.applied_fingerprint = _fingerprint(snapshot)
    doc.last_seen_fingerprint = policy
    doc.management_status = "Managed"
    doc.last_checked_on = now_datetime()
    doc.details = json.dumps(
        {"doctype": doctype, "policy": policy, "snapshot": snapshot},
        sort_keys=True,
    )
    doc.flags.ignore_permissions = True
    doc.save()


def _delete_custom_permissions(doctype: str) -> None:
    frappe.db.delete("Custom DocPerm", {"parent": doctype})


def _insert_custom_permissions(doctype: str, rows: list[dict], policy: str | None = None) -> None:
    for index, original in enumerate(rows, start=1):
        values = dict(original)
        if policy in READ_ONLY_POLICIES:
            for right in WRITE_RIGHTS:
                values[right] = 0
        elif policy == "Restricted":
            for right in ALL_RIGHTS:
                values[right] = 0

        values.update({
            "doctype": "Custom DocPerm",
            "parent": doctype,
            "parenttype": "DocType",
            "parentfield": "permissions",
            "idx": index,
        })
        frappe.get_doc(values).insert(ignore_permissions=True)


def apply_model_policy(doctype: str, policy: str) -> str:
    if frappe.session.user != "Administrator":
        frappe.throw("Only Administrator can apply model policies.", frappe.PermissionError)

    if policy in ("Enabled", "Hidden from Navigation"):
        return restore_model_policy(doctype, keep_navigation_policy=policy == "Hidden from Navigation")

    if policy not in READ_ONLY_POLICIES | {"Restricted"}:
        frappe.throw(f"Unsupported model policy: {policy}")

    state = _load_state(doctype)
    if state:
        details = frappe.parse_json(state.details) or {}
        snapshot = details.get("snapshot") or _snapshot(doctype)
    else:
        snapshot = _snapshot(doctype)

    if not snapshot.get("rows"):
        frappe.throw(f"{doctype} has no role permission rows to manage safely.")

    _delete_custom_permissions(doctype)
    _insert_custom_permissions(doctype, snapshot["rows"], policy=policy)
    _save_state(doctype, snapshot, policy)
    frappe.clear_cache(doctype=doctype)
    return policy


def restore_model_policy(doctype: str, keep_navigation_policy: bool = False) -> str:
    if frappe.session.user != "Administrator":
        frappe.throw("Only Administrator can restore model policies.", frappe.PermissionError)

    state = _load_state(doctype)
    if state:
        details = frappe.parse_json(state.details) or {}
        snapshot = details.get("snapshot") or {}
        _delete_custom_permissions(doctype)
        if snapshot.get("source") == "Custom DocPerm":
            _insert_custom_permissions(doctype, snapshot.get("rows") or [])
        frappe.delete_doc(
            "Managed Configuration State",
            state.name,
            ignore_permissions=True,
            force=True,
        )

    frappe.clear_cache(doctype=doctype)
    return "Hidden from Navigation" if keep_navigation_policy else "Enabled"


def active_native_policies() -> dict[str, str]:
    result = {}
    for row in frappe.get_all(
        "Managed Configuration State",
        filters={"component_key": ("like", f"{SNAPSHOT_PREFIX}%")},
        fields=["component_key", "details"],
    ):
        details = frappe.parse_json(row.details) or {}
        doctype = details.get("doctype") or row.component_key.removeprefix(SNAPSHOT_PREFIX)
        policy = details.get("policy")
        if doctype and policy:
            result[doctype] = policy
    return result
