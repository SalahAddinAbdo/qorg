from __future__ import annotations

import hashlib
import json

import frappe
from frappe.utils import now_datetime

from qorg.qorg.enterprise_foundation.constants import CRITICAL_DOCTYPES


def _app_owner(module: str) -> str:
    app = frappe.db.get_value("Module Def", module, "app_name") if module else None
    return app or ""


def _ownership(app: str, custom: int) -> str:
    if custom:
        return "Custom from UI"
    if app == "frappe": return "Framework Standard"
    if app == "erpnext": return "ERPNext Standard"
    if app == "hrms": return "HRMS Standard"
    if app == "qorg": return "QOrg Standard"
    return "Other App Standard"


def _kind(row) -> str:
    if row.is_virtual: return "Virtual"
    if row.istable: return "Child Table"
    if row.issingle: return "Single"
    return "Main"


def _risk(name: str, app: str, kind: str, count: int) -> str:
    if name in CRITICAL_DOCTYPES: return "Blocked"
    if app in ("frappe", "erpnext", "hrms") or kind == "Child Table": return "High"
    if count: return "Medium"
    return "Low"


def _count_records(name: str, kind: str) -> int:
    if kind in ("Single", "Virtual"):
        return 0
    try:
        return frappe.db.count(name)
    except Exception:
        return 0


def scan_models() -> list[dict]:
    rows = frappe.get_all("DocType", fields=["name", "module", "custom", "istable", "issingle", "is_virtual"], order_by="module asc, name asc")
    report_types = set(frappe.get_all("Report", pluck="ref_doctype"))
    workflow_types = set(frappe.get_all("Workflow", filters={"is_active": 1}, pluck="document_type"))
    result = []
    synchronized = now_datetime()
    for row in rows:
        app = _app_owner(row.module)
        kind = _kind(row)
        count = _count_records(row.name, kind)
        incoming = frappe.db.count("DocField", {"fieldtype": "Link", "options": row.name}) + frappe.db.count("Custom Field", {"fieldtype": "Link", "options": row.name})
        data = {
            "document_type": row.name,
            "document_label": row.name,
            "app_name": app,
            "module_name": row.module,
            "model_kind": kind,
            "ownership_type": _ownership(app, row.custom),
            "current_policy": "Enabled",
            "requested_policy": "Enabled",
            "risk_level": _risk(row.name, app, kind, count),
            "record_count": count,
            "incoming_links": incoming,
            "has_workflow": row.name in workflow_types,
            "has_reports": row.name in report_types,
            "has_workspace_links": bool(frappe.db.exists("Workspace Link", {"link_to": row.name})) if frappe.db.exists("DocType", "Workspace Link") else False,
            "last_synchronized_on": synchronized,
        }
        data["scan_fingerprint"] = hashlib.sha256(json.dumps(data, default=str, sort_keys=True).encode()).hexdigest()
        result.append(data)
    return result
