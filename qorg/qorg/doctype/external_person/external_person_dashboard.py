from __future__ import annotations

import frappe


def get_data():
    candidates = (
        ("Participation Application", ("external_person",)),
        ("Job Applicant", ("qorg_external_person",)),
        ("Volunteer Profile", ("external_person", "person", "external_person_profile")),
        ("Volunteer Application", ("external_person", "person", "applicant")),
    )

    non_standard_fieldnames = {}
    items = []
    for doctype, possible_fields in candidates:
        if not frappe.db.exists("DocType", doctype):
            continue
        meta = frappe.get_meta(doctype)
        fieldname = next(
            (fieldname for fieldname in possible_fields if meta.has_field(fieldname)),
            None,
        )
        if not fieldname:
            continue
        non_standard_fieldnames[doctype] = fieldname
        items.append(doctype)

    return {
        "fieldname": "external_person",
        "non_standard_fieldnames": non_standard_fieldnames,
        "transactions": [{"label": "Applications and Profiles", "items": items}]
        if items
        else [],
    }
