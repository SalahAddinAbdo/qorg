from __future__ import annotations

import frappe

from qorg.qorg.design_system import THEME_SCHEMA_VERSION
from qorg.qorg.design_system.service import DEFAULTS, PRESET, SETTINGS, clear_cache


PRESETS = {
    "Frappe Standard": {
        "description": "Unmodified Frappe presentation.",
        "enabled": 1,
        "theme_mode": "Follow System",
        "density": "Comfortable",
        "surface_style": "Flat",
        "content_width": "Standard",
        "navigation_style": "Standard",
    },
    "Q Org Enterprise": {
        "description": "Balanced enterprise experience for daily work.",
        "enabled": 1,
        "theme_mode": "Follow System",
        "density": "Comfortable",
        "surface_style": "Soft",
        "content_width": "Wide",
        "navigation_style": "Integrated",
    },
    "Q Org Compact": {
        "description": "Dense operations layout for tables and accounting.",
        "enabled": 1,
        "theme_mode": "Follow System",
        "density": "Compact",
        "surface_style": "Flat",
        "content_width": "Wide",
        "navigation_style": "Integrated",
    },
    "Q Org Dark": {
        "description": "Dark enterprise experience.",
        "enabled": 1,
        "theme_mode": "Dark",
        "density": "Comfortable",
        "surface_style": "Soft",
        "content_width": "Wide",
        "navigation_style": "Integrated",
    },
    "Q Org Accessible": {
        "description": "High clarity and stronger focus treatment.",
        "enabled": 1,
        "theme_mode": "Follow System",
        "density": "Comfortable",
        "surface_style": "Flat",
        "content_width": "Standard",
        "navigation_style": "Standard",
    },
}

VALUE_ALIASES = {
    "active_preset": {
        "QOrg Executive Light": "Q Org Enterprise",
        "QOrg Comfortable": "Q Org Enterprise",
        "QOrg Midnight": "Q Org Dark",
        "QOrg Compact Operations": "Q Org Compact",
        "QOrg High Contrast": "Q Org Accessible",
    },
    "theme_mode": {
        "Auto": "Follow System",
        "System": "Follow System",
        "Frappe Default": "Follow System",
    },
    "density": {
        "Standard": "Comfortable",
        "Balanced": "Comfortable",
        "Dense": "Compact",
    },
    "content_width": {
        "Frappe Default": "Standard",
        "Balanced": "Standard",
        "Wide Adaptive": "Wide",
        "Full Width": "Wide",
        "Custom": "Wide",
    },
    "navigation_style": {
        "Frappe Standard": "Standard",
        "Unified": "Integrated",
        "Enterprise": "Integrated",
    },
    "surface_style": {
        "Frappe Standard": "Flat",
        "Enterprise": "Soft",
        "Balanced": "Soft",
    },
    "login_layout": {
        "QOrg Split": "Split",
        "Full Width Split": "Split",
        "QOrg Visual": "Split",
        "QOrg Centered": "Centered",
        "QOrg Executive": "Centered",
        "QOrg Standard": "Standard",
        "Frappe Standard": "Standard",
    },
}

ALLOWED_VALUES = {
    "theme_mode": {"Follow System", "Light", "Dark"},
    "density": {"Comfortable", "Compact"},
    "content_width": {"Standard", "Wide"},
    "navigation_style": {"Standard", "Integrated"},
    "surface_style": {"Flat", "Soft", "Elevated"},
    "login_layout": {"Standard", "Split", "Centered"},
}


def ensure_presets() -> None:
    """Create or safely reconcile preset masters before Settings is saved.

    Active Preset is a Link field. Therefore, the target preset records must
    exist before any normalization can save Q Org Design System Settings.
    """
    if not frappe.db.exists("DocType", PRESET):
        return

    for name, values in PRESETS.items():
        existing = frappe.db.exists(PRESET, name)
        if existing:
            doc = frappe.get_doc(PRESET, existing)
            if not doc.get("is_system_preset"):
                # Safe adoption: keep a user-owned compatible record untouched.
                continue
        else:
            doc = frappe.new_doc(PRESET)
            doc.preset_title = name

        doc.is_system_preset = 1
        doc.managed_version = THEME_SCHEMA_VERSION
        for fieldname, value in values.items():
            if doc.meta.has_field(fieldname):
                doc.set(fieldname, value)
        doc.flags.ignore_permissions = True
        doc.save()


def normalize_settings_values(settings) -> bool:
    """Map legacy values to the compact v3 contract, idempotently."""
    changed = False

    for fieldname, aliases in VALUE_ALIASES.items():
        if not settings.meta.has_field(fieldname):
            continue
        value = settings.get(fieldname)
        mapped = aliases.get(value)
        if mapped and mapped != value:
            settings.set(fieldname, mapped)
            changed = True

    for fieldname, allowed in ALLOWED_VALUES.items():
        if not settings.meta.has_field(fieldname):
            continue
        value = settings.get(fieldname)
        if value in (None, "") or value not in allowed:
            settings.set(fieldname, DEFAULTS[fieldname])
            changed = True

    preset = settings.get("active_preset")
    mapped_preset = VALUE_ALIASES["active_preset"].get(preset)
    if mapped_preset and mapped_preset != preset:
        settings.active_preset = mapped_preset
        changed = True

    # A dangling Link must never block migrate. Presets have already been
    # ensured, so an unknown or removed preset safely falls back to Enterprise.
    if settings.meta.has_field("active_preset"):
        preset = settings.get("active_preset")
        if not preset or not frappe.db.exists(PRESET, preset):
            settings.active_preset = DEFAULTS["active_preset"]
            changed = True

    return changed


def ensure_settings() -> None:
    if not frappe.db.exists("DocType", SETTINGS):
        return

    settings = frappe.get_single(SETTINGS)
    changed = normalize_settings_values(settings)

    for fieldname, value in DEFAULTS.items():
        if settings.meta.has_field(fieldname) and settings.get(fieldname) in (None, ""):
            settings.set(fieldname, value)
            changed = True

    if changed:
        settings.flags.ignore_permissions = True
        settings.save()


def provision_design_system() -> None:
    """Provision in dependency order: Link targets, then Single settings."""
    if not frappe.db.exists("DocType", PRESET) or not frappe.db.exists("DocType", SETTINGS):
        return

    ensure_presets()
    ensure_settings()
    clear_cache()
