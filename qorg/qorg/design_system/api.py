from __future__ import annotations
import json
import frappe
from frappe import _
from frappe.utils import cint
from qorg.qorg.design_system.service import SETTINGS, PRESET, clear_cache, effective, validate_values

def _manager():
    if frappe.session.user == "Guest" or not frappe.has_permission(SETTINGS, "write"):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

@frappe.whitelist(allow_guest=True)
def get_effective_configuration(force=0):
    config=effective(use_cache=not cint(force))
    if frappe.session.user == "Guest":
        allowed={"enabled","apply_to_login","login_layout","login_image","login_title","login_subtitle","apply_to_web_forms","wide_web_forms","sticky_mobile_actions","theme_mode","density","surface_style","tokens","schema_version","fingerprint"}
        return {k:v for k,v in config.items() if k in allowed}
    return config

@frappe.whitelist(methods=["POST"])
def preview(configuration=None):
    _manager(); values=json.loads(configuration) if isinstance(configuration,str) else (configuration or {})
    config=effective(False); config.update({k:v for k,v in values.items() if k in config}); return config

@frappe.whitelist(methods=["POST"])
def apply():
    _manager(); doc=frappe.get_single(SETTINGS); validate_values(doc); clear_cache(); config=effective(False)
    frappe.publish_realtime("qorg_theme_changed", {"fingerprint":config["fingerprint"]}, after_commit=True)
    return config

@frappe.whitelist(methods=["POST"])
def restore_frappe_default():
    _manager(); doc=frappe.get_single(SETTINGS); doc.active_preset="Frappe Standard"; doc.enabled=0; doc.save(); clear_cache(); return effective(False)

@frappe.whitelist()
def validate_current_configuration():
    _manager(); validate_values(frappe.get_single(SETTINGS)); return {"valid":True,"findings":[]}

@frappe.whitelist()
def get_quick_create_menu():
    if frappe.session.user == "Guest": return {"items":[],"grouped":{}}
    settings=frappe.get_single(SETTINGS); items=[]
    for row in settings.get("quick_create_items") or []:
        dt=row.reference_doctype
        if not row.enabled or not dt or not frappe.db.exists("DocType",dt): continue
        meta=frappe.get_meta(dt)
        if meta.istable or meta.issingle or not frappe.has_permission(dt,"create"): continue
        items.append({"doctype":dt,"label":row.display_label or _(dt),"group":row.menu_group or _("Other"),"description":row.description or "","icon":row.icon or "add","favorite":cint(row.is_favorite),"sequence":row.sequence or 0})
    items.sort(key=lambda x:(not x["favorite"],x["group"],x["sequence"],x["label"]))
    grouped={}
    for item in items: grouped.setdefault(item["group"],[]).append(item)
    return {"items":items,"grouped":grouped}

@frappe.whitelist(allow_guest=True)
def get_available_languages():
    languages=frappe.get_all("Language",filters={"enabled":1},fields=["language_code","language_name"],order_by="language_name")
    return {"current":frappe.local.lang,"languages":languages}

@frappe.whitelist(methods=["POST"])
def set_current_user_language(language):
    if frappe.session.user == "Guest": frappe.throw(_("Please sign in first."),frappe.PermissionError)
    if not frappe.db.exists("Language", {"language_code":language,"enabled":1}): frappe.throw(_("Language is not enabled."))
    frappe.db.set_value("User",frappe.session.user,"language",language); frappe.clear_cache(user=frappe.session.user); return {"language":language}
