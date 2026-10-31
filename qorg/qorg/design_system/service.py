from __future__ import annotations

import hashlib
import json
from typing import Any

import frappe
from frappe.utils import cint

from qorg.qorg.design_system import THEME_SCHEMA_VERSION

SETTINGS = "Q Org Design System Settings"
PRESET = "Q Org Design Preset"
CACHE_KEY = "qorg:theme:effective:v3.1.0"

DEFAULTS = {
    "enabled": 1,
    "active_preset": "Q Org Enterprise",
    "theme_mode": "Follow System",
    "density": "Comfortable",
    "primary_color": "#137690",
    "accent_color": "#CBAE66",
    "content_width": "Wide",
    "navigation_style": "Integrated",
    "surface_style": "Soft",
    "show_create_action": 1,
    "show_language_action": 1,
    "apply_to_login": 1,
    "login_layout": "Split",
    "login_image": None,
    "login_title": "Welcome to Q Org",
    "login_subtitle": "Integrated enterprise management for your organization.",
    "apply_to_web_forms": 1,
    "wide_web_forms": 1,
    "sticky_mobile_actions": 1,
}
PUBLIC_FIELDS = tuple(DEFAULTS)

PRESET_TOKENS = {
    "Frappe Standard": {"enabled": 0},
    "Q Org Enterprise": {},
    "Q Org Compact": {"density": "Compact", "surface_style": "Flat"},
    "Q Org Dark": {"theme_mode": "Dark", "surface_style": "Soft"},
    "Q Org Accessible": {"surface_style": "Flat", "density": "Comfortable"},
}

def clear_cache() -> None:
    frappe.cache().delete_value(CACHE_KEY)

def _doc_values(doc) -> dict[str, Any]:
    return {field: doc.get(field) for field in PUBLIC_FIELDS if doc.meta.has_field(field) and doc.get(field) not in (None, "")}

def _preset_values(name: str | None) -> dict[str, Any]:
    if not name or not frappe.db.exists(PRESET, name):
        return {}
    doc = frappe.get_doc(PRESET, name)
    values = {field: doc.get(field) for field in ("theme_mode", "density", "primary_color", "accent_color", "content_width", "navigation_style", "surface_style") if doc.meta.has_field(field) and doc.get(field) not in (None, "")}
    raw = doc.get("tokens_json") if doc.meta.has_field("tokens_json") else None
    if raw:
        try: values.update(json.loads(raw))
        except (TypeError, ValueError): pass
    return values

def validate_values(doc) -> None:
    allowed = {
        "theme_mode": {"Follow System", "Light", "Dark"},
        "density": {"Comfortable", "Compact"},
        "content_width": {"Standard", "Wide"},
        "navigation_style": {"Standard", "Integrated"},
        "surface_style": {"Flat", "Soft", "Elevated"},
        "login_layout": {"Standard", "Split", "Centered"},
    }
    for field, options in allowed.items():
        value = doc.get(field)
        if value and value not in options:
            frappe.throw(f"Invalid {field}: {value}")
    for field in ("primary_color", "accent_color"):
        value = doc.get(field)
        if value and not frappe.utils.validate_json_string(json.dumps(value)):
            frappe.throw(f"Invalid {field}")

def effective(use_cache: bool = True) -> dict[str, Any]:
    if use_cache:
        cached = frappe.cache().get_value(CACHE_KEY)
        if cached: return cached if isinstance(cached, dict) else json.loads(cached)
    values = dict(DEFAULTS)
    if frappe.db.exists("DocType", SETTINGS):
        doc = frappe.get_single(SETTINGS)
        values.update(_preset_values(doc.get("active_preset")))
        values.update(_doc_values(doc))
    values["enabled"] = cint(values.get("enabled"))
    values["schema_version"] = THEME_SCHEMA_VERSION
    values["tokens"] = tokens(values)
    values["fingerprint"] = fingerprint(values)
    frappe.cache().set_value(CACHE_KEY, values, expires_in_sec=3600)
    return values

def tokens(v: dict[str, Any]) -> dict[str, str]:
    dark = v.get("theme_mode") == "Dark"
    return {
        "--qorg-brand": v.get("primary_color") or DEFAULTS["primary_color"],
        "--qorg-accent": v.get("accent_color") or DEFAULTS["accent_color"],
        "--qorg-page": "#111827" if dark else "#f5f7fa",
        "--qorg-surface": "#182230" if dark else "#ffffff",
        "--qorg-surface-muted": "#202c3c" if dark else "#f0f4f7",
        "--qorg-border": "#334155" if dark else "#d9e2e7",
        "--qorg-text": "#f3f4f6" if dark else "#163142",
        "--qorg-text-muted": "#aab6c5" if dark else "#667784",
        "--qorg-success": "#2e8b57", "--qorg-warning": "#d79b26",
        "--qorg-danger": "#bd4546", "--qorg-info": "#258bd3",
    }

def fingerprint(values: dict[str, Any]) -> str:
    raw=json.dumps({k:v for k,v in values.items() if k != "fingerprint"},sort_keys=True,default=str,separators=(",",":"))
    return hashlib.sha256(raw.encode()).hexdigest()
