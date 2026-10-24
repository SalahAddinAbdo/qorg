import json
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def provision_volunteer_management():
    required=("External Person","External Opportunity","HR Settings")
    missing=[dt for dt in required if not frappe.db.exists("DocType",dt)]
    if missing: frappe.throw("Missing required DocTypes for Volunteer and Internship Management: " + ", ".join(missing))
    path=frappe.get_app_path("qorg","qorg","volunteer_management","data","custom_fields.json")
    rows=json.load(open(path,encoding="utf-8"));grouped={}
    for row in rows:
        row=dict(row);dt=row.pop("dt")
        if frappe.db.exists("DocType",dt):grouped.setdefault(dt,[]).append(row)
    if grouped:create_custom_fields(grouped,update=True)
    for role in ("Volunteer Coordinator","Volunteer Manager"):
        if not frappe.db.exists("Role",role):frappe.get_doc({"doctype":"Role","role_name":role,"desk_access":1}).insert(ignore_permissions=True)
    _email_templates()
    from .layout import reconcile_participation_layouts
    reconcile_participation_layouts(); frappe.clear_cache()
    return {"ok": True, "roles": ["Volunteer Coordinator", "Volunteer Manager"]}


def _email_templates():
    import os
    folder=frappe.get_app_path("qorg","qorg","volunteer_management","data","email_templates")
    if not os.path.isdir(folder):return
    for fn in os.listdir(folder):
        if not fn.endswith(".json"):continue
        data=json.load(open(os.path.join(folder,fn),encoding="utf-8"));name=data["name"]
        if not frappe.db.exists("Email Template",name):frappe.get_doc(data).insert(ignore_permissions=True)
