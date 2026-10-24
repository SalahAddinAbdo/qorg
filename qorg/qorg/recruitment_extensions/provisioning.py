import hashlib
import json
import os
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from .constants import CONFIGURATION_VERSION

def provision_recruitment_extensions():
    _custom_fields();_email_templates()
    from .layout_provisioning import reconcile_recruitment_form_layouts
    reconcile_recruitment_form_layouts();frappe.clear_cache()
def _custom_fields():
    path=frappe.get_app_path("qorg","qorg","recruitment_extensions","data","custom_fields.json");rows=json.load(open(path,encoding="utf-8"));grouped={}
    for row in rows:
        row=dict(row);dt=row.pop("dt");grouped.setdefault(dt,[]).append(row)
    for dt,defs in grouped.items():
        if frappe.db.exists("DocType",dt):create_custom_fields({dt:defs},update=True)
def _email_templates():
    folder=frappe.get_app_path("qorg","qorg","recruitment_extensions","data","email_templates")
    for filename in sorted(os.listdir(folder)):
        if not filename.endswith(".json"):continue
        data=json.load(open(os.path.join(folder,filename),encoding="utf-8"));name=data["name"];digest=hashlib.sha256(json.dumps(data,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        if not frappe.db.exists("Email Template",name):
            frappe.get_doc(data).insert(ignore_permissions=True)
        else:
            template=frappe.get_doc("Email Template",name)
            # Upgrade only templates still marked as managed defaults. Manual templates are preserved.
            if template.meta.has_field("qorg_managed_template") and template.get("qorg_managed_template"):
                template.subject=data.get("subject");template.response_html=data.get("response_html");template.use_html=1
                if template.meta.has_field("qorg_managed_hash"):template.qorg_managed_hash=digest
                template.flags.ignore_permissions=True;template.save()
