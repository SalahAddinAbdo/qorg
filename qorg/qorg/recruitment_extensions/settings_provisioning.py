import json
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def _load(name):
    path=frappe.get_app_path("qorg","qorg","recruitment_extensions","data",name)
    return json.load(open(path,encoding="utf-8"))

def provision_recruitment_settings():
    if not frappe.db.exists("DocType","HR Settings"):
        return
    fields=_load("hr_settings_custom_fields.json")
    first=next((f for f in fields if f["fieldname"]=="qorg_recruitment_defaults_tab"),None)
    if first:
        meta=frappe.get_meta("HR Settings")
        first["insert_after"]=meta.fields[-1].fieldname if meta.fields else ""
    create_custom_fields({"HR Settings":fields},update=True)
    grouped={}
    for row in _load("recruitment_settings_operational_fields.json"):
        row=dict(row);dt=row.pop("dt")
        if frappe.db.exists("DocType",dt):
            grouped.setdefault(dt,[]).append(row)
    if grouped:
        create_custom_fields(grouped,update=True)
    frappe.clear_cache()
