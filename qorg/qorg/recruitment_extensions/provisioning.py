import json, frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from .constants import CONFIGURATION_VERSION

def provision_recruitment_extensions():
    _custom_fields(); _email_templates(); frappe.clear_cache()

def _custom_fields():
    path=frappe.get_app_path("qorg","qorg","recruitment_extensions","data","custom_fields.json")
    rows=json.load(open(path,encoding="utf-8")); grouped={}
    for r in rows:
        r=dict(r); dt=r.pop("dt"); grouped.setdefault(dt,[]).append(r)
    for dt,defs in grouped.items():
        if frappe.db.exists("DocType",dt): create_custom_fields({dt:defs},update=True)

def _email_templates():
    folder=frappe.get_app_path("qorg","qorg","recruitment_extensions","data","email_templates")
    import os
    for fn in os.listdir(folder):
        if not fn.endswith('.json'): continue
        data=json.load(open(os.path.join(folder,fn),encoding='utf-8')); name=data['name']
        if not frappe.db.exists("Email Template",name): frappe.get_doc(data).insert(ignore_permissions=True)
