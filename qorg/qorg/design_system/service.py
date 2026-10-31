from __future__ import annotations

import frappe

SETTINGS = "Q Org Design System Settings"
PRESET = "Q Org Design Preset"
BASELINE_PRESET = "Frappe Standard"
LEGACY_CACHE_KEYS = (
    "qorg:design-system:effective:v2.9.3",
    "qorg:design-system:effective:v2.9.3.3.3",
    "qorg:theme:effective:v3.0.0",
    "qorg:theme:effective:v3.1.0",
    "qorg:theme:effective:v3.1.1",
    "qorg:theme:effective:v3.1.2",
    "qorg:theme:effective:v3.1.3",
)


def clear_legacy_theme_cache() -> None:
    for key in LEGACY_CACHE_KEYS:
        frappe.cache().delete_value(key)


def baseline_status() -> dict:
    settings = frappe.get_single(SETTINGS)
    return {
        "baseline": True,
        "enabled": int(settings.get("enabled") or 0),
        "active_preset": settings.get("active_preset"),
        "show_language_action": int(settings.get("show_language_action") or 0),
        "quick_create_items": len(settings.get("quick_create_items") or []),
    }
