from __future__ import annotations

import json
from pathlib import Path

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from qorg.qorg.people_and_opportunities.web_form_definitions import MANAGED_VERSION, WEB_FORMS
from qorg.qorg.people_and_opportunities.web_form_design import apply_managed_design

SECURITY = {
    "published": 1,
    "login_required": 1,
    "allow_delete": 0,
    "anonymous": 0,
}


def provision_standard_opportunity_web_forms():
    _create_custom_fields()
    result = {"created": [], "updated": [], "preserved_css": []}
    for definition in WEB_FORMS:
        if not frappe.db.exists("DocType", definition["doc_type"]):
            continue
        route = definition["route"]
        name = frappe.db.get_value("Web Form", {"route": route}, "name")
        if name:
            doc = frappe.get_doc("Web Form", name)
            status = "updated"
        else:
            doc = frappe.new_doc("Web Form")
            status = "created"

        _apply_base(doc, definition)
        _reconcile_fields(doc, definition)
        _clear_client_script(doc)
        design_status = apply_managed_design(doc)
        doc.save(ignore_permissions=True) if not doc.is_new() else doc.insert(ignore_permissions=True)
        result[status].append(route)
        if design_status == "preserved":
            result["preserved_css"].append(route)

    frappe.clear_cache(doctype="Web Form")
    return result


def _create_custom_fields():
    path = Path(__file__).resolve().parent / "data" / "web_form_architecture_custom_fields.json"
    create_custom_fields(json.loads(path.read_text(encoding="utf-8")), update=True)


def _apply_base(doc, definition):
    values = {
        "title": definition["title"],
        "route": definition["route"],
        "doc_type": definition["doc_type"],
        "module": "QOrg",
        "is_standard": 0,
        "allow_multiple": definition["allow_multiple"],
        "allow_edit": definition["allow_edit"],
        "show_list": definition["show_list"],
        "allow_print": definition["allow_print"],
        "introduction_text": definition["introduction_text"],
        "success_message": definition["success_message"],
        "apply_document_permissions": 0,
    }
    values.update(SECURITY)
    for fieldname, value in values.items():
        if doc.meta.has_field(fieldname):
            doc.set(fieldname, value)


def _clear_client_script(doc):
    if doc.meta.has_field("client_script"):
        doc.client_script = ""


def _reconcile_fields(doc, definition):
    table_field = next(
        (f.fieldname for f in doc.meta.fields if f.fieldtype == "Table" and f.options == "Web Form Field"),
        None,
    )
    if not table_field:
        frappe.throw("Web Form Field table was not found.")

    child_meta = frappe.get_meta(doc.meta.get_field(table_field).options)
    target_meta = frappe.get_meta(definition["doc_type"])
    rows = {row.fieldname: row for row in doc.get(table_field) or [] if row.fieldname}

    for fieldname in definition["candidate_fields"]:
        target = target_meta.get_field(fieldname)
        if not target or target.fieldtype in ("Section Break", "Column Break", "Tab Break"):
            continue
        row = rows.get(fieldname) or doc.append(table_field, {})
        _child_set(row, child_meta, "fieldname", fieldname)
        if not rows.get(fieldname):
            _child_set(row, child_meta, "label", target.label or fieldname)
            _child_set(row, child_meta, "fieldtype", target.fieldtype)
            _child_set(row, child_meta, "options", target.options)
            _child_set(row, child_meta, "description", target.description)
        _child_set(row, child_meta, "reqd", int(fieldname in definition["required_fields"]))
        _child_set(row, child_meta, "read_only", int(fieldname in definition["read_only_fields"]))


def _child_set(row, meta, fieldname, value):
    if meta.has_field(fieldname):
        row.set(fieldname, value)
