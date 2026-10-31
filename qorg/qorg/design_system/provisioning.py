from __future__ import annotations
import json
import frappe
from qorg.qorg.design_system import THEME_SCHEMA_VERSION
from qorg.qorg.design_system.service import PRESET, SETTINGS, DEFAULTS, clear_cache

PRESETS = {
 "Frappe Standard": {"description":"Unmodified Frappe presentation.","enabled":0,"theme_mode":"Follow System","density":"Comfortable","surface_style":"Flat","content_width":"Standard","navigation_style":"Standard"},
 "Q Org Enterprise": {"description":"Balanced enterprise experience for daily work.","theme_mode":"Follow System","density":"Comfortable","surface_style":"Soft","content_width":"Wide","navigation_style":"Integrated"},
 "Q Org Compact": {"description":"Dense operations layout for tables and accounting.","theme_mode":"Follow System","density":"Compact","surface_style":"Flat","content_width":"Wide","navigation_style":"Integrated"},
 "Q Org Dark": {"description":"Dark enterprise experience.","theme_mode":"Dark","density":"Comfortable","surface_style":"Soft","content_width":"Wide","navigation_style":"Integrated"},
 "Q Org Accessible": {"description":"High clarity and stronger focus treatment.","theme_mode":"Follow System","density":"Comfortable","surface_style":"Flat","content_width":"Standard","navigation_style":"Standard"},
}

def provision_design_system():
    if not frappe.db.exists("DocType", PRESET) or not frappe.db.exists("DocType", SETTINGS): return
    for name, values in PRESETS.items():
        existing=frappe.db.exists(PRESET,name)
        if existing:
            doc=frappe.get_doc(PRESET,existing)
            if not doc.get("is_system_preset"): continue
        else:
            doc=frappe.new_doc(PRESET); doc.preset_title=name
        doc.enabled=1; doc.is_system_preset=1; doc.managed_version=THEME_SCHEMA_VERSION
        for field,value in values.items():
            if doc.meta.has_field(field): doc.set(field,value)
        doc.flags.ignore_permissions=True; doc.save()
    settings=frappe.get_single(SETTINGS)
    changed=False
    for field,value in DEFAULTS.items():
        if settings.meta.has_field(field) and settings.get(field) in (None,""):
            settings.set(field,value); changed=True
    if settings.meta.has_field("schema_version"): settings.schema_version=THEME_SCHEMA_VERSION; changed=True
    if changed:
        settings.flags.ignore_permissions=True; settings.save()
    clear_cache()
