from __future__ import annotations

import hashlib
import json
from pathlib import Path

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from qorg.qorg.people_and_opportunities.web_form_definitions import (
    MANAGED_VERSION,
    WEB_FORMS,
)

SECURITY_SETTINGS = {
    "published": 1,
    "login_required": 1,
    "allow_delete": 0,
    "anonymous": 0,
}


def provision_standard_opportunity_web_forms():
    _create_custom_fields()
    result = {"created": [], "updated": [], "preserved_custom": [], "removed_fields": []}
    for definition in WEB_FORMS:
        if not frappe.db.exists("DocType", definition["doc_type"]):
            continue
        status = _reconcile_web_form(definition, result)
        result[status].append(definition["route"])
    frappe.clear_cache(doctype="Web Form")
    return result


def _create_custom_fields():
    path = Path(__file__).resolve().parent / "data" / "web_form_custom_fields.json"
    create_custom_fields(json.loads(path.read_text(encoding="utf-8")), update=True)


def _reconcile_web_form(definition, result):
    name = frappe.db.get_value("Web Form", {"route": definition["route"]}, "name")
    if not name:
        doc = frappe.new_doc("Web Form")
        _apply_new_web_form(doc, definition)
        doc.insert(ignore_permissions=True)
        return "created"

    doc = frappe.get_doc("Web Form", name)
    customized = _is_customized(doc)
    _apply_security_settings(doc, definition)
    removed = _reconcile_fields(doc, definition, customized)
    result["removed_fields"].extend(
        f"{definition['route']}:{fieldname}" for fieldname in removed
    )

    if not customized:
        _apply_managed_presentation(doc, definition)
        status = "updated"
    else:
        _set_if_field(doc, "qorg_managed_update_available", 1)
        status = "preserved_custom"

    _set_if_field(doc, "qorg_managed_default", 1)
    _set_if_field(doc, "qorg_managed_version", MANAGED_VERSION)
    _set_if_field(doc, "qorg_managed_hash", _managed_hash(doc))
    doc.save(ignore_permissions=True)
    return status


def _apply_new_web_form(doc, definition):
    _set_if_field(doc, "title", definition["title"])
    _set_if_field(doc, "route", definition["route"])
    _set_if_field(doc, "doc_type", definition["doc_type"])
    _set_if_field(doc, "module", "QOrg")
    _set_if_field(doc, "is_standard", 0)
    _apply_security_settings(doc, definition)
    _apply_managed_presentation(doc, definition)
    _reconcile_fields(doc, definition, customized=False)
    _set_if_field(doc, "qorg_managed_default", 1)
    _set_if_field(doc, "qorg_managed_version", MANAGED_VERSION)
    _set_if_field(doc, "qorg_managed_update_available", 0)
    _set_if_field(doc, "qorg_managed_hash", _managed_hash(doc))


def _apply_security_settings(doc, definition):
    _set_if_field(doc, "doc_type", definition["doc_type"])
    _set_if_field(doc, "route", definition["route"])
    for fieldname, value in SECURITY_SETTINGS.items():
        _set_if_field(doc, fieldname, value)
    for key in ("allow_multiple", "allow_edit", "show_list", "allow_print"):
        _set_if_field(doc, key, definition.get(key, 0))
    _set_if_field(doc, "apply_document_permissions", 0)


def _apply_managed_presentation(doc, definition):
    for fieldname, key in (
        ("title", "title"),
        ("introduction_text", "introduction_text"),
        ("success_message", "success_message"),
        ("client_script", "client_script"),
    ):
        _set_if_field(doc, fieldname, definition.get(key))
    _set_if_field(doc, "qorg_managed_update_available", 0)


def _reconcile_fields(doc, definition, customized):
    table_field = _web_form_fields_table(doc)
    if not table_field:
        frappe.throw("Web Form field table was not found in the installed Frappe version.")

    child_meta = frappe.get_meta(doc.meta.get_field(table_field).options)
    target_meta = frappe.get_meta(definition["doc_type"])
    current_rows = {row.fieldname: row for row in doc.get(table_field) or [] if row.fieldname}
    removed = []

    for fieldname in definition.get("remove_fields", []):
        row = current_rows.get(fieldname)
        if row:
            doc.remove(row)
            removed.append(fieldname)

    for fieldname in definition["candidate_fields"]:
        target_field = target_meta.get_field(fieldname)
        if not target_field or target_field.fieldtype in ("Section Break", "Column Break", "Tab Break"):
            continue
        row = current_rows.get(fieldname)
        if not row:
            row = doc.append(table_field, {})
            _set_child_value(row, child_meta, "fieldname", fieldname)
            _set_child_value(row, child_meta, "label", target_field.label or fieldname)
            _set_child_value(row, child_meta, "fieldtype", target_field.fieldtype)
            _set_child_value(row, child_meta, "options", target_field.options)
            _set_child_value(row, child_meta, "description", target_field.description)
        if not customized:
            _set_child_value(row, child_meta, "label", target_field.label or fieldname)
            _set_child_value(row, child_meta, "fieldtype", target_field.fieldtype)
            _set_child_value(row, child_meta, "options", target_field.options)
            _set_child_value(row, child_meta, "description", target_field.description)
        _set_child_value(row, child_meta, "reqd", int(fieldname in definition.get("required_fields", [])))
        _set_child_value(row, child_meta, "read_only", int(fieldname in definition.get("read_only_fields", [])))
    return removed


def _web_form_fields_table(doc):
    for field in doc.meta.fields:
        if field.fieldtype == "Table" and field.options == "Web Form Field":
            return field.fieldname
    return None


def _set_child_value(row, meta, fieldname, value):
    if meta.has_field(fieldname):
        row.set(fieldname, value)


def _is_customized(doc):
    if not doc.meta.has_field("qorg_managed_hash"):
        return True
    stored = doc.get("qorg_managed_hash")
    if not stored:
        return False
    return stored != _managed_hash(doc)


def _managed_hash(doc):
    table_field = _web_form_fields_table(doc)
    rows = []
    if table_field:
        for row in doc.get(table_field) or []:
            rows.append({
                "fieldname": row.get("fieldname"),
                "label": row.get("label"),
                "fieldtype": row.get("fieldtype"),
                "options": row.get("options"),
                "reqd": row.get("reqd"),
                "read_only": row.get("read_only"),
                "idx": row.get("idx"),
            })
    payload = {
        "title": doc.get("title"),
        "route": doc.get("route"),
        "doc_type": doc.get("doc_type"),
        "introduction_text": doc.get("introduction_text"),
        "success_message": doc.get("success_message"),
        "client_script": doc.get("client_script"),
        "fields": rows,
    }
    raw = json.dumps(payload, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _set_if_field(doc, fieldname, value):
    if doc.meta.has_field(fieldname):
        doc.set(fieldname, value)
