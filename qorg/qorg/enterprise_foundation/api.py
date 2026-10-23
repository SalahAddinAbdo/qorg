from __future__ import annotations

import json

import frappe
from frappe.utils import now_datetime

from qorg.qorg.enterprise_foundation.audit import (
    audit_company_settings as _audit_company,
    audit_control_center as _audit_center,
)
from qorg.qorg.enterprise_foundation.constants import CONFIGURATION_VERSION, CRITICAL_DOCTYPES
from qorg.qorg.enterprise_foundation.model_registry import scan_models
from qorg.qorg.enterprise_foundation.permissions import require_administrator


def _center():
    require_administrator()
    return frappe.get_single("Feature Control Center")


@frappe.whitelist()
def synchronize_models():
    doc = _center()
    existing = {row.document_type: row for row in (doc.models or [])}
    doc.set("models", [])

    for data in scan_models():
        old = existing.get(data["document_type"])
        if old:
            data.update(
                {
                    "requested_policy": old.requested_policy or data["current_policy"],
                    "requested_action_policy": old.requested_action_policy
                    or data["current_action_policy"],
                    "change_reason": old.change_reason,
                }
            )
        doc.append("models", data)

    doc.last_synchronized_on = now_datetime()
    doc.last_synchronized_by = frappe.session.user
    doc.configuration_version = CONFIGURATION_VERSION
    doc.pending_change_count = sum(1 for row in doc.models if _row_changed(row))
    doc.flags.ignore_permissions = True
    doc.save()
    return {"models": len(doc.models), "pending": doc.pending_change_count}


def _current_action_config(row, applied_actions: dict) -> dict:
    return applied_actions.get(
        row.document_type,
        {
            "policy": "Standard",
            "allow_print": 1,
            "allow_email": 1,
            "allow_comments": 1,
            "allow_attachments": 1,
        },
    )


def _action_config_changed(row, applied_actions: dict) -> bool:
    current = _current_action_config(row, applied_actions)
    return any(
        (
            current.get("policy", "Standard") != (row.requested_action_policy or "Standard"),
            int(current.get("allow_print", 1)) != int(row.allow_print or 0),
            int(current.get("allow_email", 1)) != int(row.allow_email or 0),
            int(current.get("allow_comments", 1)) != int(row.allow_comments or 0),
            int(current.get("allow_attachments", 1)) != int(row.allow_attachments or 0),
        )
    )


def _row_changed(row, applied_actions: dict | None = None) -> bool:
    if row.current_policy != row.requested_policy:
        return True
    if applied_actions is None:
        return row.current_action_policy != row.requested_action_policy
    return _action_config_changed(row, applied_actions)


def _build_model_changes(doc):
    from qorg.qorg.enterprise_foundation.model_policy_engine import active_action_policies

    applied_actions = active_action_policies()
    changes = []
    for row in doc.models or []:
        if not _row_changed(row, applied_actions):
            continue
        allowed = row.document_type not in CRITICAL_DOCTYPES and row.risk_level != "Blocked"
        changes.append(
            {
                "document_type": row.document_type,
                "access_from": row.current_policy,
                "access_to": row.requested_policy,
                "action_from": _current_action_config(row, applied_actions),
                "action_to": {
                    "policy": row.requested_action_policy,
                    "allow_print": int(row.allow_print or 0),
                    "allow_email": int(row.allow_email or 0),
                    "allow_comments": int(row.allow_comments or 0),
                    "allow_attachments": int(row.allow_attachments or 0),
                },
                "allowed": allowed,
                "risk": row.risk_level,
                "reason": row.change_reason,
            }
        )
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


@frappe.whitelist(methods=["POST"])
def apply_model_changes():
    doc = _center()
    preview = _build_model_changes(doc)
    blocked = [change for change in preview if not change["allowed"]]
    if blocked:
        frappe.throw("Blocked or critical model changes must be removed before applying.")

    from qorg.qorg.enterprise_foundation.model_policy_engine import (
        active_action_policies,
        active_native_policies,
        apply_action_policy,
        apply_model_policy,
    )

    applied_actions = active_action_policies()
    applied = []
    for row in doc.models or []:
        access_changed = row.current_policy != row.requested_policy
        action_changed = _action_config_changed(row, applied_actions)
        if not access_changed and not action_changed:
            continue
        if not row.change_reason:
            frappe.throw(f"Change reason is required for {row.document_type}.")

        current_action = _current_action_config(row, applied_actions)
        native_utility_changed = any((
            int(current_action.get("allow_print", 1)) != int(row.allow_print or 0),
            int(current_action.get("allow_email", 1)) != int(row.allow_email or 0),
        ))

        if access_changed or (native_utility_changed and row.requested_policy in ("Read Only", "Feature Disabled", "Deprecated")):
            row.current_policy = apply_model_policy(
                row.document_type, row.requested_policy, row.allow_print, row.allow_email
            )
            row.requested_policy = row.current_policy

        if action_changed:
            row.current_action_policy = apply_action_policy(
                row.document_type,
                row.requested_action_policy,
                allow_print=row.allow_print,
                allow_email=row.allow_email,
                allow_comments=row.allow_comments,
                allow_attachments=row.allow_attachments,
            )
            row.requested_action_policy = row.current_action_policy

        applied.append(row.document_type)

    access = active_native_policies()
    actions = active_action_policies()
    doc.last_preview = json.dumps(preview, default=str, indent=2)
    doc.pending_change_count = 0
    doc.last_apply_summary = (
        f"Applied {len(applied)} model changes. "
        f"Active access policies: {len(access)}. "
        f"Active action policies: {len(actions)}."
    )
    doc.flags.ignore_permissions = True
    doc.save()
    frappe.clear_cache()
    frappe.publish_realtime(
        "qorg_model_policy_changed",
        {"changed": applied, "access": access, "actions": actions},
        after_commit=True,
    )
    return {"applied": applied, "access": access, "actions": actions}


@frappe.whitelist()
def audit_control_center():
    doc = _center()
    doc.set("audit_results", [])
    for finding in _audit_center(doc):
        doc.append("audit_results", finding)
    doc.flags.ignore_permissions = True
    doc.save()
    return {"findings": len(doc.audit_results)}


@frappe.whitelist()
def get_model_policies():
    from qorg.qorg.enterprise_foundation.model_policy_engine import active_native_policies

    return active_native_policies()


@frappe.whitelist()
def get_action_policies():
    from qorg.qorg.enterprise_foundation.model_policy_engine import active_action_policies

    return active_action_policies()


@frappe.whitelist()
def audit_company_settings(settings_name: str):
    require_administrator()
    doc = frappe.get_doc("Company Feature Settings", settings_name)
    issues = _audit_company(doc)
    doc.last_audited_on = now_datetime()
    doc.last_audit_summary = "\n".join(issues) if issues else "No configuration issues detected."
    doc.flags.ignore_permissions = True
    doc.save()
    return {"issues": issues}
