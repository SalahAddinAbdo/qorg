from __future__ import annotations
import json
from pathlib import Path
import frappe
REQUIRED_STANDARD_DOCTYPES=("Company","Contact","Address","Language","Country","Gender","User","Employee","Job Opening","Job Applicant","Employment Type","Department","Designation","Project","Print Format","Skill")
ROLES=("Opportunity User","Opportunity Manager","Volunteer Coordinator","Volunteer Manager")
def _data(name): return json.loads(Path(__file__).parent.joinpath("data",name).read_text())
def provision_people_opportunities_core():
    missing=[dt for dt in REQUIRED_STANDARD_DOCTYPES if not frappe.db.exists("DocType",dt)]
    if missing: frappe.throw("Missing required standard DocTypes: " + ", ".join(missing))
    for role in ROLES:
        if not frappe.db.exists("Role",role): frappe.get_doc({"doctype":"Role","role_name":role,"desk_access":1}).insert(ignore_permissions=True)
    for spec in _data("custom_fields.json"):
        if not frappe.db.exists("DocType", spec["dt"]):
            continue
        name=f"{spec['dt']}-{spec['fieldname']}"; existing=frappe.db.exists("Custom Field",name)
        values=dict(spec); values.update({"doctype":"Custom Field","name":name,"is_system_generated":1,"module":"QOrg"})
        if existing:
            doc=frappe.get_doc("Custom Field",name)
            if doc.fieldtype!=spec["fieldtype"] or (spec.get("options") and doc.options!=spec.get("options")): frappe.throw(f"Incompatible Custom Field {name}")
            doc.is_system_generated=1; doc.module="QOrg"; doc.flags.ignore_permissions=True; doc.save()
        else: frappe.get_doc(values).insert(ignore_permissions=True)
    _ensure_masters(); _ensure_print_format(); frappe.clear_cache()
def _ensure_masters():
    rows=(("Employment","Employment",1),("Volunteering","Volunteering",2),("Internship","Internship",3),("Consultancy","Consultancy",4),("Other","Other",5))
    for name,behavior,order in rows:
        if not frappe.db.exists("External Opportunity Type",name): frappe.get_doc({"doctype":"External Opportunity Type","type_name":name,"behavior_code":behavior,"display_order":order,"enabled":1,"allow_publication":1,"allow_external_application":1}).insert(ignore_permissions=True)
    categories = (
        ("General Volunteering", 1, None),
        ("Community Service", 0, "General Volunteering"),
        ("Technical Support", 0, "General Volunteering"),
        ("Field Operations", 0, "General Volunteering"),
    )
    for name, is_group, parent in categories:
        if frappe.db.exists("Volunteer Category", name):
            continue
        category = frappe.get_doc(
            {
                "doctype": "Volunteer Category",
                "category_name": name,
                "is_group": is_group,
                "parent_volunteer_category": parent,
                "enabled": 1,
            }
        )
        category.flags.ignore_permissions = True
        category.insert()

def _ensure_print_format():
    name="External Person CV"
    if frappe.db.exists("Print Format",name): return
    html=Path(__file__).parent.joinpath("templates","external_person_cv.html").read_text()
    frappe.get_doc({"doctype":"Print Format","name":name,"doc_type":"External Person","print_format_type":"Jinja","html":html,"standard":"No","custom_format":1}).insert(ignore_permissions=True)


def reconcile_external_profile_ownership():
    from qorg.qorg.doctype.external_person.external_person import (
        reconcile_unlinked_external_profiles,
    )
    return reconcile_unlinked_external_profiles()
