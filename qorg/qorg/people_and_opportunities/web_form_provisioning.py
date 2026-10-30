from __future__ import annotations

import json
from pathlib import Path

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from qorg.qorg.people_and_opportunities.web_form_definitions import WEB_FORMS
from qorg.qorg.people_and_opportunities.web_form_design import apply_managed_design
from qorg.qorg.people_and_opportunities.web_form_grid_policies import provision_external_profile_grid_policies

SECURITY = {"published": 1, "login_required": 1, "allow_delete": 0, "anonymous": 0}
LAYOUT_TYPES = {"Page Break", "Section Break", "Column Break"}

OBSOLETE_CUSTOM_FIELDS = {
    "Website Settings": {
        "qorg_web_form_show_hero_header",
        "qorg_web_form_show_privacy_notice",
        "qorg_web_form_emphasize_header",
        "qorg_web_form_emphasize_introduction",
    },
    "Web Form": {
        "qorg_web_form_hero_mode",
        "qorg_web_form_privacy_notice_mode",
        "qorg_web_form_header_mode",
        "qorg_web_form_introduction_mode",
    },
}


def cleanup_obsolete_web_form_design_fields():
    deleted = []
    for doctype, fieldnames in OBSOLETE_CUSTOM_FIELDS.items():
        for fieldname in sorted(fieldnames):
            custom_field_name = frappe.db.get_value(
                "Custom Field",
                {"dt": doctype, "fieldname": fieldname},
                "name",
            )
            if custom_field_name:
                frappe.delete_doc(
                    "Custom Field",
                    custom_field_name,
                    ignore_permissions=True,
                    force=True,
                )
                deleted.append(f"{doctype}.{fieldname}")

            for property_setter in frappe.get_all(
                "Property Setter",
                filters={"doc_type": doctype, "field_name": fieldname},
                pluck="name",
            ):
                frappe.delete_doc(
                    "Property Setter",
                    property_setter,
                    ignore_permissions=True,
                    force=True,
                )
    return deleted


def provision_standard_opportunity_web_forms():
    deleted = cleanup_obsolete_web_form_design_fields()
    _create_custom_fields()
    provision_external_profile_grid_policies()
    result = {
        "created": [],
        "updated": [],
        "deleted_obsolete_fields": deleted,
    }
    for definition in WEB_FORMS:
        if frappe.db.exists("DocType", definition["doc_type"]):
            _provision_one(definition, result)
    frappe.clear_cache(doctype="Website Settings")
    frappe.clear_cache(doctype="Web Form")
    return result


def _create_custom_fields():
    path = Path(__file__).resolve().parent / "data" / "web_form_architecture_custom_fields.json"
    create_custom_fields(json.loads(path.read_text(encoding="utf-8")), update=True)


def _provision_one(definition, result):
    name = frappe.db.get_value("Web Form", {"route": definition["route"]}, "name")
    doc = frappe.get_doc("Web Form", name) if name else frappe.new_doc("Web Form")
    status = "updated" if name else "created"
    _apply_base(doc, definition)
    _rebuild_layout(doc, definition)
    _ensure_application_profile_confirmation(doc, definition)
    if doc.meta.has_field("client_script"):
        doc.client_script = ""
    apply_managed_design(doc, force=True)
    doc.save(ignore_permissions=True) if name else doc.insert(ignore_permissions=True)
    result[status].append(definition["route"])


def _apply_base(doc, definition):
    values = {
        "title": definition["title"], "route": definition["route"],
        "doc_type": definition["doc_type"], "module": "QOrg", "is_standard": 0,
        "allow_multiple": definition["allow_multiple"], "allow_edit": definition["allow_edit"],
        "show_list": definition["show_list"], "allow_print": definition["allow_print"],
        "introduction_text": definition["introduction_text"],
        "success_message": definition["success_message"], "apply_document_permissions": 0,
        "button_label": definition.get("submit_button_label"),
    }
    values.update(SECURITY)
    for fieldname, value in values.items():
        if doc.meta.has_field(fieldname) and value is not None:
            doc.set(fieldname, value)


def _rebuild_layout(doc, definition):
    table_field = next((f.fieldname for f in doc.meta.fields if f.fieldtype == "Table" and f.options == "Web Form Field"), None)
    if not table_field:
        frappe.throw("Web Form Field table was not found.")
    child_meta = frappe.get_meta(doc.meta.get_field(table_field).options)
    target_meta = frappe.get_meta(definition["doc_type"])
    doc.set(table_field, [])
    layout_index = 0

    for item in definition["layout"]:
        fieldtype = item.get("fieldtype")
        if fieldtype in LAYOUT_TYPES:
            layout_index += 1
            row = doc.append(table_field, {})
            # Frappe validates Page Break fieldnames against the target DocType.
            # A synthetic fieldname therefore makes the Web Form invalid. Page
            # Break rows are layout-only and must keep fieldname empty. Section
            # and Column Break rows may retain a stable technical fieldname.
            if fieldtype != "Page Break":
                _set(row, child_meta, "fieldname", f"qorg_layout_{layout_index}")
            _set(row, child_meta, "fieldtype", fieldtype)
            _set(row, child_meta, "label", item.get("label") or "")
            continue

        fieldname = item["fieldname"]
        target = target_meta.get_field(fieldname)
        if not target:
            continue
        row = doc.append(table_field, {})
        _set(row, child_meta, "fieldname", fieldname)
        _set(row, child_meta, "fieldtype", target.fieldtype)
        _set(row, child_meta, "label", item.get("label") or target.label or fieldname)
        _set(row, child_meta, "options", target.options)
        _set(row, child_meta, "description", target.description)
        _set(row, child_meta, "reqd", int(item.get("required", False)))
        _set(row, child_meta, "read_only", int(item.get("read_only", False)))
        if target.fieldtype == "Link":
            _set(row, child_meta, "allow_read_on_all_link_options", 1)


def _set(row, meta, fieldname, value):
    if meta.has_field(fieldname):
        row.set(fieldname, value)


def _ensure_application_profile_confirmation(doc, definition):
    if definition.get("doc_type") != "Participation Application":
        return
    table_field = next(
        (f.fieldname for f in doc.meta.fields if f.fieldtype == "Table" and f.options == "Web Form Field"),
        None,
    )
    if not table_field:
        return
    rows = doc.get(table_field) or []
    if any(row.fieldname == "profile_review_confirmed" for row in rows):
        return
    child_meta = frappe.get_meta(doc.meta.get_field(table_field).options)
    row = doc.append(table_field, {})
    _set(row, child_meta, "fieldname", "profile_review_confirmed")
    _set(row, child_meta, "fieldtype", "Check")
    _set(row, child_meta, "label", "I confirm that I reviewed my profile and that its information and documents are current and accurate")
    _set(row, child_meta, "description", "Review and update your external profile before submitting this application.")
    _set(row, child_meta, "reqd", 1)
    _set(row, child_meta, "read_only", 0)
