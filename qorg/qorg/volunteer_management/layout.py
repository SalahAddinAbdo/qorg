from __future__ import annotations

import json

import frappe


def _layout_anchor(doctype, managed_fields):
    """Append the managed block after existing fields without reordering standard fields."""
    meta = frappe.get_meta(doctype)
    candidates = [
        field.fieldname
        for field in meta.fields
        if field.fieldname and field.fieldname not in managed_fields
    ]
    return candidates[-1] if candidates else ""


def reconcile_participation_layouts():
    path = frappe.get_app_path(
        "qorg",
        "qorg",
        "volunteer_management",
        "data",
        "form_layouts.json",
    )
    with open(path, encoding="utf-8") as source:
        plans = json.load(source)

    changed = []
    for doctype, fields in plans.items():
        managed_fields = set(fields)
        previous = _layout_anchor(doctype, managed_fields)

        for fieldname in fields:
            name = f"{doctype}-{fieldname}"
            if not frappe.db.exists("Custom Field", name):
                continue

            current = frappe.db.get_value(
                "Custom Field",
                name,
                "insert_after",
            ) or ""
            if current != previous:
                frappe.db.set_value(
                    "Custom Field",
                    name,
                    "insert_after",
                    previous,
                    update_modified=False,
                )
                changed.append(name)
            previous = fieldname

        frappe.clear_cache(doctype=doctype)

    return {"changed": changed, "count": len(changed)}
