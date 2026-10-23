from __future__ import annotations

import hashlib
import json

import frappe
from frappe.utils import now_datetime

from qorg.qorg.enterprise_foundation.constants import CRITICAL_DOCTYPES
from qorg.qorg.enterprise_foundation.model_policy_engine import (
    active_action_policies,
    active_native_policies,
)

# Technical and framework metadata that should not be managed as operational models.
EXCLUDED_DOCTYPES = frozenset(
    {
        "DocType",
        "DocField",
        "Custom Field",
        "Property Setter",
        "Custom DocPerm",
        "DocPerm",
        "Module Def",
        "Installed Applications",
        "Patch Log",
        "Error Log",
        "Scheduled Job Log",
        "Route History",
        "Prepared Report",
        "RQ Job",
        "RQ Worker",
        "Version",
    }
)


def _app_owner(module: str) -> str:
    return frappe.db.get_value("Module Def", module, "app_name") if module else ""


def _ownership(app: str, custom: int) -> str:
    if custom:
        return "Custom from UI"
    return {
        "frappe": "Framework Standard",
        "erpnext": "ERPNext Standard",
        "hrms": "HRMS Standard",
        "qorg": "QOrg Standard",
    }.get(app, "Other App Standard")


def _kind(row) -> str:
    if row.is_virtual:
        return "Virtual"
    if row.issingle:
        return "Single"
    return "Main"


def _risk(name: str, app: str, kind: str, count: int) -> str:
    if name in CRITICAL_DOCTYPES:
        return "Blocked"
    if app in ("frappe", "erpnext", "hrms"):
        return "High"
    if kind == "Virtual":
        return "High"
    return "Medium" if count else "Low"


def _record_count(name: str, kind: str) -> int:
    if kind in ("Single", "Virtual"):
        return 0
    try:
        return frappe.db.count(name)
    except Exception:
        return 0


def _incoming_links(name: str) -> int:
    return frappe.db.count("DocField", {"fieldtype": "Link", "options": name}) + frappe.db.count(
        "Custom Field", {"fieldtype": "Link", "options": name}
    )


def scan_models() -> list[dict]:
    """Return only independently usable DocTypes.

    Child Tables are deliberately excluded because their records and write lifecycle
    belong to the parent DocType. Reports, Pages and Workspaces are navigation
    components and remain governed by their native role/workspace settings rather
    than being mixed into document access policies.
    """

    rows = frappe.get_all(
        "DocType",
        filters={"istable": 0},
        fields=["name", "module", "custom", "issingle", "is_virtual"],
        order_by="module asc, name asc",
    )
    rows = [row for row in rows if row.name not in EXCLUDED_DOCTYPES]

    access_policies = active_native_policies()
    action_policies = active_action_policies()
    report_types = set(frappe.get_all("Report", pluck="ref_doctype"))
    workflow_types = set(
        frappe.get_all("Workflow", filters={"is_active": 1}, pluck="document_type")
    )
    synchronized_on = now_datetime()
    result = []

    for row in rows:
        app = _app_owner(row.module)
        kind = _kind(row)
        count = _record_count(row.name, kind)
        access_policy = access_policies.get(row.name, "Enabled")
        action = action_policies.get(row.name, {})

        data = {
            "document_type": row.name,
            "document_label": row.name,
            "app_name": app,
            "module_name": row.module,
            "model_kind": kind,
            "ownership_type": _ownership(app, row.custom),
            "current_policy": access_policy,
            "requested_policy": access_policy,
            "current_action_policy": action.get("policy", "Standard"),
            "requested_action_policy": action.get("policy", "Standard"),
            "risk_level": _risk(row.name, app, kind, count),
            "record_count": count,
            "incoming_links": _incoming_links(row.name),
            "has_workflow": row.name in workflow_types,
            "has_reports": row.name in report_types,
            "has_workspace_links": bool(
                frappe.db.exists("Workspace Link", {"link_to": row.name})
            )
            if frappe.db.exists("DocType", "Workspace Link")
            else False,
            "allow_print": action.get("allow_print", 1),
            "allow_email": action.get("allow_email", 1),
            "allow_comments": action.get("allow_comments", 1),
            "allow_attachments": action.get("allow_attachments", 1),
            "last_synchronized_on": synchronized_on,
        }
        data["scan_fingerprint"] = hashlib.sha256(
            json.dumps(data, default=str, sort_keys=True).encode()
        ).hexdigest()
        result.append(data)

    return result
