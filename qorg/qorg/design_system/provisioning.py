from __future__ import annotations

import frappe
from qorg.qorg.design_system.service import BASELINE_PRESET, PRESET, SETTINGS

def ensure_frappe_standard_preset():
    name=frappe.db.exists(PRESET,BASELINE_PRESET)
    doc=frappe.get_doc(PRESET,name) if name else frappe.new_doc(PRESET)
    if doc.meta.has_field("preset_title") and not doc.get("preset_title"): doc.preset_title=BASELINE_PRESET
    if doc.meta.has_field("enabled"): doc.enabled=1
    if doc.meta.has_field("is_system_preset"): doc.is_system_preset=1
    if doc.meta.has_field("baseline_status"): doc.baseline_status="Frappe Standard"
    if doc.meta.has_field("description"): doc.description="Frappe Standard Desk baseline."
    doc.flags.ignore_permissions=True; doc.save()

def provision_login_experience():
    if not frappe.db.exists("DocType",SETTINGS) or not frappe.db.exists("DocType",PRESET): return
    ensure_frappe_standard_preset()
    doc=frappe.get_single(SETTINGS); changed=False
    defaults={"enabled":0,"active_preset":BASELINE_PRESET,"show_language_action":1,"enable_login_experience":1,"show_login_language_switcher":1,"login_background_position":"Center","login_overlay_strength":"Medium","login_text_color":"Light","login_visual_title":"Q Org","login_visual_subtitle":"Integrated enterprise management for your organization.","login_form_title":"Welcome","login_form_subtitle":"Sign in to continue"}
    for field,value in defaults.items():
        if doc.meta.has_field(field) and (doc.get(field) in (None,"") or field in {"enabled","active_preset"}):
            if doc.get(field)!=value: doc.set(field,value); changed=True
    if changed: doc.flags.ignore_permissions=True; doc.save()
