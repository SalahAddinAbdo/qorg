from __future__ import annotations

import json

import frappe
from frappe.utils import now_datetime

from qorg.qorg.enterprise_foundation.audit import audit_company_settings as _audit_company, audit_control_center as _audit_center
from qorg.qorg.enterprise_foundation.constants import CONFIGURATION_VERSION, CRITICAL_DOCTYPES
from qorg.qorg.enterprise_foundation.model_registry import scan_models
from qorg.qorg.enterprise_foundation.permissions import require_administrator


def _center():
    require_administrator()
    return frappe.get_single("Feature Control Center")


@frappe.whitelist()
def synchronize_models():
    doc=_center()
    existing={row.document_type:row for row in (doc.models or [])}
    doc.set("models", [])
    for data in scan_models():
        old=existing.get(data["document_type"])
        if old:
            data["requested_policy"]=old.requested_policy or "Enabled"
            data["change_reason"]=old.change_reason
            data["current_policy"]=old.current_policy or "Enabled"
        doc.append("models", data)
    doc.last_synchronized_on=now_datetime(); doc.last_synchronized_by=frappe.session.user
    doc.configuration_version=CONFIGURATION_VERSION
    doc.pending_change_count=sum(1 for r in doc.models if r.current_policy != r.requested_policy)
    doc.flags.ignore_permissions=True; doc.save()
    return {"models":len(doc.models),"pending":doc.pending_change_count}


@frappe.whitelist()
def audit_control_center():
    doc=_center(); doc.set("audit_results", [])
    for finding in _audit_center(doc): doc.append("audit_results", finding)
    doc.flags.ignore_permissions=True; doc.save()
    return {"findings":len(doc.audit_results)}


def _build_model_changes(doc):
    changes = []
    for row in doc.models or []:
        if row.current_policy == row.requested_policy:
            continue
        allowed = row.document_type not in CRITICAL_DOCTYPES and row.risk_level != "Blocked"
        changes.append({
            "document_type": row.document_type,
            "from": row.current_policy,
            "to": row.requested_policy,
            "allowed": allowed,
            "risk": row.risk_level,
            "reason": row.change_reason,
        })
    return changes


@frappe.whitelist()
def preview_model_changes():
    doc = _center()
    changes = _build_model_changes(doc)
    doc.last_preview = json.dumps(changes, default=str, indent=2)
    doc.pending_change_count = len(changes)
    doc.flags.ignore_permissions = True
    doc.save()
    return changes


@frappe.whitelist()
def apply_model_changes():
    doc = _center()
    preview = _build_model_changes(doc)
    blocked = [change for change in preview if not change["allowed"]]
    if blocked:
        frappe.throw("Blocked or critical model changes must be removed before applying.")

    applied = []
    for row in doc.models or []:
        if row.current_policy == row.requested_policy:
            continue
        if not row.change_reason:
            frappe.throw(f"Change reason is required for {row.document_type}.")
        row.current_policy = row.requested_policy
        applied.append(row.document_type)

    doc.last_preview = json.dumps(preview, default=str, indent=2)
    doc.pending_change_count = 0
    doc.last_apply_summary = f"Applied {len(applied)} managed model policies."
    doc.flags.ignore_permissions = True
    doc.save()
    frappe.clear_cache()
    frappe.publish_realtime(
        "qorg_model_policy_changed",
        {"changed": applied},
        after_commit=True,
    )
    return {"applied": applied}


@frappe.whitelist()
def restore_managed_defaults():
    doc=_center(); restored=0
    for row in doc.models or []:
        if row.app_name == "qorg" and row.current_policy != "Enabled":
            row.requested_policy="Enabled"; row.current_policy="Enabled"; restored+=1
    doc.last_apply_summary=f"Restored {restored} QOrg managed model policies."
    doc.flags.ignore_permissions=True; doc.save(); frappe.clear_cache()
    return {"restored":restored}


@frappe.whitelist()
def export_configuration():
    doc=_center()
    return {"configuration_version":doc.configuration_version,"site_features":[r.as_dict() for r in doc.site_features],"models":[r.as_dict() for r in doc.models]}


@frappe.whitelist()
def audit_company_settings(settings_name: str):
    require_administrator()
    doc=frappe.get_doc("Company Feature Settings", settings_name)
    issues = _audit_company(doc)
    doc.last_audited_on = now_datetime()
    doc.last_audit_summary = "\n".join(issues) if issues else "No configuration issues detected."
    doc.flags.ignore_permissions=True; doc.save()
    return {"issues":issues}


@frappe.whitelist()
def get_model_policy(document_type: str):
    from qorg.qorg.enterprise_foundation.policy_enforcement import get_model_policy as _get_policy
    return {"document_type": document_type, "policy": _get_policy(document_type)}


@frappe.whitelist()
def resolve_company_feature(company: str, feature_key: str):
    require_administrator()
    from qorg.qorg.enterprise_foundation.features import resolve_feature_state
    return resolve_feature_state(company, feature_key)


@frappe.whitelist()
def get_model_policies():
    from qorg.qorg.enterprise_foundation.policy_enforcement import get_policy_map
    return get_policy_map()
