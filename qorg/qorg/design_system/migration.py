import hashlib
import frappe

OBSOLETE_WEBSITE_FIELDS=("qorg_enable_enhanced_web_form_design","qorg_web_form_use_company_branding","qorg_web_form_show_hero_header","qorg_web_form_show_privacy_notice","qorg_web_form_sticky_actions","qorg_web_form_hide_child_row_name","qorg_web_form_max_content_width","qorg_web_form_header_style","qorg_web_form_default_company")
OBSOLETE_WEB_FORM_FIELDS=("qorg_managed_css_hash","qorg_managed_css_version","qorg_managed_css_update_available","qorg_apply_managed_web_form_design")

def migrate_legacy_web_form_design():
    _migrate_settings(); _migrate_web_forms(); _delete_obsolete_fields()

def _migrate_settings():
    if not frappe.db.exists("DocType","Q Org Design System Settings") or not frappe.db.exists("DocType","Website Settings"): return
    settings=frappe.get_single("Q Org Design System Settings"); old=frappe.get_single("Website Settings")
    mapping={"qorg_enable_enhanced_web_form_design":"apply_to_qorg_web_components","qorg_web_form_sticky_actions":"web_form_sticky_actions","qorg_web_form_hide_child_row_name":"web_form_hide_technical_child_row_name","qorg_web_form_max_content_width":"web_form_max_content_width"}
    changed=False
    for source,target in mapping.items():
        if old.meta.has_field(source) and settings.meta.has_field(target) and old.get(source) not in (None,""):
            settings.set(target,old.get(source)); changed=True
    if changed: settings.flags.ignore_permissions=True; settings.save()

def _migrate_web_forms():
    if not frappe.db.exists("DocType","Web Form"): return
    for name in frappe.get_all("Web Form",pluck="name"):
        doc=frappe.get_doc("Web Form",name); css=doc.custom_css or ""; stored=doc.get("qorg_managed_css_hash") if doc.meta.has_field("qorg_managed_css_hash") else None
        current=hashlib.sha256(css.encode()).hexdigest() if css else ""
        if css and stored and current==stored:
            doc.custom_css=""; doc.flags.ignore_permissions=True; doc.save()
        # User-modified and unknown CSS is intentionally preserved.

def _delete_obsolete_fields():
    for dt,fields in (("Website Settings",OBSOLETE_WEBSITE_FIELDS),("Web Form",OBSOLETE_WEB_FORM_FIELDS)):
        for fieldname in fields:
            name=f"{dt}-{fieldname}"
            if frappe.db.exists("Custom Field",name): frappe.delete_doc("Custom Field",name,ignore_permissions=True,force=True)
