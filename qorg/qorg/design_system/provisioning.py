from __future__ import annotations

import frappe

from qorg.qorg.design_system.service import (
    BASELINE_PRESET, PRESET, SETTINGS, clear_legacy_theme_cache,
)


def ensure_frappe_standard_preset() -> None:
    if not frappe.db.exists("DocType", PRESET):
        return
    name = frappe.db.exists(PRESET, BASELINE_PRESET)
    if name:
        doc = frappe.get_doc(PRESET, name)
    else:
        doc = frappe.new_doc(PRESET)
        doc.preset_title = BASELINE_PRESET
    if doc.meta.has_field("enabled"):
        doc.enabled = 1
    if doc.meta.has_field("is_system_preset"):
        doc.is_system_preset = 1
    if doc.meta.has_field("description"):
        doc.description = "Frappe Standard baseline. No custom Q Org theme assets are loaded."
    if doc.meta.has_field("baseline_status"):
        doc.baseline_status = "Frappe Standard"
    doc.flags.ignore_permissions = True
    doc.save()


def provision_baseline_records() -> None:
    if not frappe.db.exists("DocType", SETTINGS) or not frappe.db.exists("DocType", PRESET):
        return
    ensure_frappe_standard_preset()
    settings = frappe.get_single(SETTINGS)
    changed = False
    if settings.get("enabled"):
        settings.enabled = 0
        changed = True
    if settings.get("active_preset") != BASELINE_PRESET:
        settings.active_preset = BASELINE_PRESET
        changed = True
    if settings.get("show_language_action") in (None, ""):
        settings.show_language_action = 1
        changed = True
    if changed:
        settings.flags.ignore_permissions = True
        settings.save()
    clear_legacy_theme_cache()
