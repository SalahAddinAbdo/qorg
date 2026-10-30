from __future__ import annotations

import json
from pathlib import Path

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from qorg.qorg.people_and_opportunities.web_form_definitions import WEB_FORMS
from qorg.qorg.people_and_opportunities.web_form_grid_policies import (
    provision_external_profile_grid_policies,
)

LAYOUT_TYPES = {"Page Break", "Section Break", "Column Break"}


def provision_standard_opportunity_web_forms():
    _create_custom_fields()
    provision_external_profile_grid_policies()
    result = {"created": [], "updated": []}
    for definition in WEB_FORMS:
        if frappe.db.exists("DocType", definition["doc_type"]):
            _provision_one(definition, result)
    frappe.clear_cache(doctype="Web Form")
    return result


def _create_custom_fields():
    data_dir = Path(__file__).resolve().parent / "data"
    for filename in ("web_form_architecture_custom_fields.json", "web_form_design_custom_fields.json"):
        path = data_dir / filename
        if path.exists():
            create_custom_fields(json.loads(path.read_text(encoding="utf-8")), update=True)


def _provision_one(definition, result):
    name = frappe.db.get_value("Web Form", {"route": definition["route"]}, "name")
    doc = frappe.get_doc("Web Form", name) if name else frappe.new_doc("Web Form")
    status = "updated" if name else "created"
    _apply_settings(doc, definition)
    _rebuild_fields(doc, definition)
    if doc.meta.has_field("client_script"):
        doc.client_script = ""
    if name:
        doc.save(ignore_permissions=True)
    else:
        doc.insert(ignore_permissions=True)
    result[status].append(definition["route"])


def _apply_settings(doc, definition):
    values = {
        "title": definition["title"],
        "route": definition["route"],
        "doc_type": definition["doc_type"],
        "module": "QOrg",
        "is_standard": 0,
        "published": 1,
        "login_required": 1,
        "anonymous": 0,
        "allow_multiple": definition["allow_multiple"],
        "allow_edit": definition["allow_edit"],
        "allow_delete": 0,
        "show_list": definition["show_list"],
        "allow_print": definition["allow_print"],
        "apply_document_permissions": 0,
        "introduction_text": definition["introduction_text"],
        "success_message": definition["success_message"],
        "button_label": definition.get("submit_button_label"),
    }
    for fieldname, value in values.items():
        if doc.meta.has_field(fieldname):
            doc.set(fieldname, value)
    if doc.meta.has_field("key_required"):
        doc.key_required = int(definition.get("key_required", 0))


def _rebuild_fields(doc, definition):
    table_field = next(
        (f.fieldname for f in doc.meta.fields if f.fieldtype == "Table" and f.options == "Web Form Field"),
        None,
    )
    if not table_field:
        frappe.throw("Web Form Field table was not found.")
    child_meta = frappe.get_meta(doc.meta.get_field(table_field).options)
    target_meta = frappe.get_meta(definition["doc_type"])
    doc.set(table_field, [])
    layout_index = 0

    for item in definition["layout"]:
        fieldtype = item.get("fieldtype")
        row = doc.append(table_field, {})
        if fieldtype in LAYOUT_TYPES:
            layout_index += 1
            if fieldtype != "Page Break":
                _set(row, child_meta, "fieldname", f"qorg_layout_{layout_index}")
            _set(row, child_meta, "fieldtype", fieldtype)
            _set(row, child_meta, "label", item.get("label") or "")
            continue

        target = target_meta.get_field(item["fieldname"])
        if not target:
            frappe.throw(
                f"{definition['doc_type']} is missing managed field {item['fieldname']}"
            )
        _set(row, child_meta, "fieldname", target.fieldname)
        _set(row, child_meta, "fieldtype", target.fieldtype)
        _set(row, child_meta, "label", item.get("label") or target.label or target.fieldname)
        _set(row, child_meta, "options", target.options)
        _set(row, child_meta, "description", target.description)
        _set(row, child_meta, "reqd", int(item.get("required", False)))
        _set(row, child_meta, "read_only", int(item.get("read_only", False)))
        if target.fieldtype == "Link":
            _set(row, child_meta, "allow_read_on_all_link_options", 1)


def _set(row, meta, fieldname, value):
    if meta.has_field(fieldname):
        row.set(fieldname, value)
