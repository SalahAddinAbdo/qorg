from __future__ import annotations

import frappe
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

POLICIES = {
    "education": ["qualification", "institution", "country", "graduation_year"],
    "experience": ["organization", "job_title", "from_date", "to_date"],
    "training": ["course_title", "provider", "start_date", "end_date"],
    "languages": ["language", "reading", "writing", "speaking"],
    "skills": ["skill", "proficiency", "years_of_experience"],
    "volunteer_experience": ["organization", "role", "from_date", "to_date"],
    "references": ["reference_name", "organization", "email", "mobile_no"],
}


def provision_external_profile_grid_policies():
    if not frappe.db.exists("DocType", "External Person"):
        return {"updated": []}

    parent_meta = frappe.get_meta("External Person")
    updated = []
    for table_fieldname, visible_fields in POLICIES.items():
        table_field = parent_meta.get_field(table_fieldname)
        if not table_field or table_field.fieldtype != "Table" or not table_field.options:
            continue
        child_meta = frappe.get_meta(table_field.options)
        for df in child_meta.fields:
            visible = df.fieldname in visible_fields
            _set(df.parent, df.fieldname, "in_list_view", "1" if visible else "0", "Check")
            if visible:
                columns = 2 if len(visible_fields) >= 4 else 3
                _set(df.parent, df.fieldname, "columns", str(columns), "Int")
            if df.fieldname == "page_break":
                _set(df.parent, df.fieldname, "print_hide", "1", "Check")
        updated.append(table_field.options)
    frappe.clear_cache(doctype="External Person")
    return {"updated": updated}


def _set(doctype, fieldname, property_name, value, property_type):
    make_property_setter(
        doctype,
        fieldname,
        property_name,
        value,
        property_type,
        for_doctype=False,
        validate_fields_for_doctype=False,
    )
