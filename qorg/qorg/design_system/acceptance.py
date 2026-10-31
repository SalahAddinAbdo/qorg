from __future__ import annotations

import hashlib
import json
from typing import Any

import frappe

from qorg.qorg.design_system import DESIGN_SYSTEM_SCHEMA_VERSION
from qorg.qorg.design_system.service import PRESET, SETTINGS, VISUAL_FIELDS, effective, validate_values

REQUIRED_PRESETS = (
    "Frappe Standard",
    "QOrg Executive Light",
    "QOrg Midnight",
    "QOrg Compact Operations",
    "QOrg High Contrast",
)
REQUIRED_ASSETS = (
    "qorg_navigation_alignment.bundle.js",
    "qorg_design_system.bundle.js",
    "qorg_design_admin.bundle.js",
    "qorg_design_system.bundle.scss",
    "qorg_website_design.bundle.js",
    "qorg_website_design.bundle.scss",
)


def audit_runtime_configuration() -> dict[str, Any]:
    """Return one deterministic, read-only acceptance report for the installed site."""
    checks: list[dict[str, Any]] = []

    def add(name: str, passed: bool, detail: Any = None, severity: str = "Error") -> None:
        checks.append({"name": name, "passed": bool(passed), "severity": severity, "detail": detail})

    add("Settings DocType exists", bool(frappe.db.exists("DocType", SETTINGS)), SETTINGS)
    add("Preset DocType exists", bool(frappe.db.exists("DocType", PRESET)), PRESET)
    if not frappe.db.exists("DocType", SETTINGS) or not frappe.db.exists("DocType", PRESET):
        return _finish(checks)

    settings = frappe.get_single(SETTINGS)
    try:
        validate_values(settings)
        add("Settings values are valid", True)
    except Exception as error:
        add("Settings values are valid", False, str(error))

    preset_names = set(frappe.get_all(PRESET, filters={"enabled": 1}, pluck="name"))
    for name in REQUIRED_PRESETS:
        add(f"Required preset: {name}", name in preset_names, name)

    preset_meta = frappe.get_meta(PRESET)
    missing_preset_fields = sorted(field for field in VISUAL_FIELDS if not preset_meta.has_field(field))
    add("Preset schema covers all visual fields", not missing_preset_fields, missing_preset_fields)

    active = settings.get("active_preset")
    add("Active preset is valid", not active or bool(frappe.db.exists(PRESET, active)), active)

    config = effective(use_cache=False)
    add("Effective configuration enabled value is boolean", config.get("enabled") in (True, False, 0, 1), config.get("enabled"))
    add("Effective configuration has CSS variables", bool(config.get("css_variables")), len(config.get("css_variables") or {}))

    required_visual_fields = {
        "control_height_policy", "small_text_height_policy", "focus_ring_style",
        "page_width_policy", "app_rail_style", "module_sidebar_style",
        "navbar_search_style", "workspace_content_width", "workspace_grid_policy",
        "workspace_card_style", "workspace_card_height_policy", "workspace_heading_accent",
        "nested_surface_policy", "section_action_style", "mixed_content_bidi_safety",
    }
    missing_unified_fields = sorted(required_visual_fields - set(VISUAL_FIELDS))
    add("Unified Polish fields are registered", not missing_unified_fields, missing_unified_fields)
    expected_variables = {
        "--qorg-control-height", "--qorg-small-text-min-height", "--qorg-text-editor-min-height",
        "--qorg-page-max-width", "--qorg-app-rail-icon-size", "--qorg-module-sidebar-width",
        "--qorg-navigation-item-height", "--qorg-workspace-column-gap", "--qorg-workspace-row-gap",
    }
    css_variables = config.get("css_variables") or {}
    missing_variables = sorted(expected_variables - set(css_variables))
    add("Unified Polish CSS variables are generated", not missing_variables, missing_variables)
    add("Action Dock has a visible action", not config.get("enable_action_dock") or bool(config.get("show_create_action") or config.get("show_language_action")), {
        "enabled": config.get("enable_action_dock"), "create": config.get("show_create_action"), "language": config.get("show_language_action"),
    })
    add("Unified Polish page width is configured", config.get("page_width_policy") in {"Wide Adaptive", "Balanced", "Full Width", "Custom", "Frappe Default"}, config.get("page_width_policy"))
    add("Unified Polish workspace grid is configured", config.get("workspace_grid_policy") in {"Adaptive", "Content Based", "Two Columns", "Three Columns", "Frappe Default"}, config.get("workspace_grid_policy"))
    add("Universal interface polish is enabled", bool(config.get("sticky_list_header") and config.get("enable_action_dock")), {
        "sticky_list_header": config.get("sticky_list_header"), "action_dock": config.get("enable_action_dock"),
    })
    if frappe.db.exists("DocType", "Web Form"):
        published = frappe.db.count("Web Form", {"published": 1})
        add("Published Web Forms discovered", True, published, "Info")

    if frappe.db.exists("DocType", "Website Theme"):
        theme = frappe.db.get_single_value("Website Settings", "website_theme") if frappe.db.exists("DocType", "Website Settings") else None
        add("Website Theme integration", True, theme or "Frappe Standard", "Info")

    quick_items = settings.get("quick_create_items") or []
    duplicate_doctypes = sorted({row.reference_doctype for row in quick_items if row.reference_doctype and sum(1 for item in quick_items if item.reference_doctype == row.reference_doctype) > 1})
    add("Quick Create items are unique", not duplicate_doctypes, duplicate_doctypes)

    fingerprint_payload = {field: config.get(field) for field in sorted(VISUAL_FIELDS)}
    fingerprint = hashlib.sha256(json.dumps(fingerprint_payload, sort_keys=True, default=str).encode()).hexdigest()
    report = _finish(checks)
    report.update({
        "schema_version": DESIGN_SYSTEM_SCHEMA_VERSION,
        "site": frappe.local.site,
        "active_preset": active,
        "configuration_fingerprint": fingerprint,
        "visual_fields": len(VISUAL_FIELDS),
        "required_assets": REQUIRED_ASSETS,
    })
    return report


def audit_idempotency_snapshot() -> dict[str, Any]:
    """Create a stable snapshot to compare before and after a second migrate."""
    counts = {}
    for doctype in (SETTINGS, PRESET, "Q Org Quick Create Item"):
        if frappe.db.exists("DocType", doctype):
            counts[doctype] = 1 if frappe.get_meta(doctype).issingle else frappe.db.count(doctype)
    report = audit_runtime_configuration()
    return {
        "schema_version": report.get("schema_version"),
        "configuration_fingerprint": report.get("configuration_fingerprint"),
        "counts": counts,
        "required_presets": {name: bool(frappe.db.exists(PRESET, name)) for name in REQUIRED_PRESETS},
    }


def _finish(checks: list[dict[str, Any]]) -> dict[str, Any]:
    failures = [row for row in checks if not row["passed"] and row["severity"] in {"Error", "Blocked"}]
    return {
        "valid": not failures,
        "checks_total": len(checks),
        "checks_passed": sum(1 for row in checks if row["passed"]),
        "checks_failed": len(failures),
        "checks": checks,
    }
