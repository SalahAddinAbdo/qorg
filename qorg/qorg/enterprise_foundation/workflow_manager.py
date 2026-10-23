from __future__ import annotations

import hashlib
import json

import frappe
from frappe.utils import now_datetime


def _normalized_workflow(doc_or_dict) -> dict:
    if hasattr(doc_or_dict, "as_dict"):
        data = doc_or_dict.as_dict(no_nulls=True)
    else:
        data = dict(doc_or_dict)
    return {
        "workflow_name": data.get("workflow_name"),
        "document_type": data.get("document_type"),
        "is_active": int(data.get("is_active") or 0),
        "workflow_state_field": data.get("workflow_state_field"),
        "send_email_alert": int(data.get("send_email_alert") or 0),
        "states": sorted([{k:r.get(k) for k in ("state","doc_status","allow_edit","update_field","update_value") if r.get(k) not in (None,"")} for r in data.get("states",[])], key=lambda x:(x.get("state") or "", x.get("doc_status") or 0)),
        "transitions": sorted([{k:r.get(k) for k in ("state","action","next_state","allowed","allow_self_approval","condition") if r.get(k) not in (None,"")} for r in data.get("transitions",[])], key=lambda x:(x.get("state") or "",x.get("action") or "",x.get("next_state") or "")),
    }


def workflow_fingerprint(doc_or_dict) -> str:
    payload=json.dumps(_normalized_workflow(doc_or_dict), sort_keys=True, separators=(",",":"), default=str)
    return hashlib.sha256(payload.encode()).hexdigest()


def ensure_managed_workflow(definition: dict, version: str, known_legacy_fingerprints: tuple[str,...]=()) -> str:
    name=definition["workflow_name"]
    key=f"Workflow::{name}"
    desired=workflow_fingerprint(definition)
    state=frappe.db.exists("Managed Configuration State", key)
    existing_name=frappe.db.get_value("Workflow", {"workflow_name":name}, "name")
    if not existing_name:
        doc=frappe.get_doc({"doctype":"Workflow", **definition}).insert(ignore_permissions=True)
        _save_state(key, version, desired, workflow_fingerprint(doc), "Managed", {"created": True})
        return "created"
    current_doc=frappe.get_doc("Workflow", existing_name)
    current=workflow_fingerprint(current_doc)
    if state:
        old=frappe.get_doc("Managed Configuration State", state)
        safe=current == old.applied_fingerprint
    else:
        safe=current == desired or current in set(known_legacy_fingerprints)
    if safe:
        _apply_definition(current_doc, definition)
        current_doc.save(ignore_permissions=True)
        actual=workflow_fingerprint(current_doc)
        _save_state(key, version, desired, actual, "Managed", {"upgraded": True})
        return "updated" if current != actual else "unchanged"
    _save_state(key, version, desired, current, "Administrator Modified", {"desired_fingerprint":desired})
    return "preserved"


def _apply_definition(doc, definition):
    for key in ("document_type","is_active","workflow_state_field","send_email_alert"):
        if key in definition: doc.set(key, definition[key])
    doc.set("states", [])
    for row in definition.get("states",[]): doc.append("states", row)
    doc.set("transitions", [])
    for row in definition.get("transitions",[]): doc.append("transitions", row)


def _save_state(key, version, desired, actual, status, details):
    if frappe.db.exists("Managed Configuration State", key):
        doc=frappe.get_doc("Managed Configuration State", key)
    else:
        doc=frappe.new_doc("Managed Configuration State")
        doc.component_type="Workflow"; doc.component_key=key
    doc.managed_version=version
    doc.applied_fingerprint=actual
    doc.last_seen_fingerprint=actual
    doc.management_status=status
    doc.last_checked_on=now_datetime()
    doc.details=json.dumps(details, sort_keys=True)
    doc.save(ignore_permissions=True)
