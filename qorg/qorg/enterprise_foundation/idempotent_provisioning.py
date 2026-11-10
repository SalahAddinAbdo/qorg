from __future__ import annotations

from typing import Any

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

IGNORED_DEFINITION_KEYS = {"doctype", "name", "creation", "modified", "modified_by", "owner", "idx"}


def _normal(value: Any):
    if value is None:
        return ""
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, str):
        return value.replace("\r\n", "\n").strip()
    return value


def _custom_field_differs(doctype: str, definition: dict) -> bool:
    fieldname = definition.get("fieldname")
    if not fieldname:
        return False
    name = f"{doctype}-{fieldname}"
    if not frappe.db.exists("Custom Field", name):
        return True
    current = frappe.get_cached_doc("Custom Field", name)
    for key, desired in definition.items():
        if key in IGNORED_DEFINITION_KEYS or not current.meta.has_field(key):
            continue
        if _normal(current.get(key)) != _normal(desired):
            return True
    return False


def create_custom_fields_if_changed(definitions: dict, update: bool = True):
    """Create or update only missing/different Custom Fields.

    Unchanged definitions never call Frappe's writer, so modified/modified_by remain stable.
    Returns a compact audit result for acceptance tests and migration logs.
    """
    pending = {}
    unchanged = []
    for doctype, fields in (definitions or {}).items():
        if not frappe.db.exists("DocType", doctype):
            continue
        for definition in fields or []:
            if _custom_field_differs(doctype, definition):
                pending.setdefault(doctype, []).append(definition)
            else:
                unchanged.append(f"{doctype}-{definition.get('fieldname')}")
    if pending:
        create_custom_fields(pending, update=update)
    return {
        "changed": [f"{dt}-{row.get('fieldname')}" for dt, rows in pending.items() for row in rows],
        "unchanged": unchanged,
    }

VOLATILE_DOC_KEYS = {
    "creation", "modified", "modified_by", "owner", "docstatus", "doctype",
    "__islocal", "__unsaved", "__onload", "_user_tags", "_comments", "_assign",
    "_liked_by", "_seen", "idx", "parent", "parentfield", "parenttype",
}


def normalized_document_state(doc):
    """Stable recursive state used to avoid no-op document saves."""
    def clean(value):
        if isinstance(value, dict):
            return {
                key: clean(item)
                for key, item in sorted(value.items())
                if key not in VOLATILE_DOC_KEYS
            }
        if isinstance(value, list):
            return [clean(item) for item in value]
        return _normal(value)
    return clean(doc.as_dict(no_nulls=False))


def save_document_if_changed(doc, before_state, ignore_permissions=True):
    """Save only when managed content differs; return True only for a real write."""
    if normalized_document_state(doc) == before_state:
        return False
    doc.save(ignore_permissions=ignore_permissions)
    return True
