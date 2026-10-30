from __future__ import annotations

import hashlib
import json
import re
from typing import Any

import frappe
from frappe import _
from frappe.utils import cint, now

from qorg.qorg.design_system import DESIGN_SYSTEM_SCHEMA_VERSION

SETTINGS = "Q Org Design System Settings"
PRESET = "Q Org Design Preset"
CACHE_KEY = "qorg:design-system:effective:v2"

ENUMS = {
    "theme_mode_policy": {"Follow Frappe/System", "Light", "Dark"},
    "density": {"Frappe Default", "Comfortable", "Compact"},
    "typography_policy": {"Frappe Default", "System UI", "QOrg Bundled"},
    "heading_weight": {"Default", "Medium", "Semibold"},
    "line_height_scale": {"Default", "Comfortable", "Spacious"},
    "control_radius": {"Frappe Default", "Compact", "Subtle", "Rounded"},
    "button_radius": {"Frappe Default", "Compact", "Subtle", "Rounded"},
    "card_radius": {"Frappe Default", "Compact", "Subtle", "Rounded"},
    "dialog_radius": {"Frappe Default", "Compact", "Subtle", "Rounded"},
    "border_strength": {"Frappe Default", "Subtle", "Defined"},
    "elevation_scale": {"Frappe Default", "Flat", "Subtle", "Elevated"},
    "workspace_card_density": {"Frappe Default", "Comfortable", "Compact"},
    "dialog_width_policy": {"Frappe Default", "Adaptive"},
    "status_indicator_strength": {"Frappe Default", "Enhanced"},
    "contrast_policy": {"Frappe Default", "WCAG AA Guard"},
    "touch_target_policy": {"Frappe Default", "Enhanced"},
    "login_layout": {"Frappe Standard", "QOrg Split", "QOrg Centered", "QOrg Visual"},
    "login_visual_source": {"None", "Managed Image", "Gradient"},
    "login_mobile_visual_policy": {"Hide", "Compact Header", "Show Below Form"},
    "experience_style": {"QOrg Executive", "QOrg Midnight", "QOrg Operations", "Frappe Standard"},
    "surface_hierarchy": {"Layered", "Subtle", "Flat"},
    "navigation_emphasis": {"Balanced", "Brand Forward", "Minimal"},
    "page_header_style": {"Executive", "Compact", "Frappe Standard"},
    "section_presentation": {"Structured", "Soft Cards", "Frappe Standard"},
    "table_presentation": {"Enterprise", "Compact Operations", "Frappe Standard"},
    "action_dock_desktop_placement": {"Auto", "Sidebar Footer", "Floating Edge"},
    "action_dock_mobile_placement": {"Floating Orb", "Bottom Bar"},
    "action_dock_collapsed_behavior": {"Icons Only", "Expand on Hover"},
    "form_control_style": {"Enterprise", "Compact Operations", "Frappe Standard"},
    "toolbar_style": {"Unified", "Compact", "Frappe Standard"},
    "grid_style": {"Enterprise", "Compact Operations", "Frappe Standard"},
    "alternate_view_style": {"Enterprise", "Subtle", "Frappe Standard"},
    "dialog_style": {"Enterprise", "Compact", "Frappe Standard"},
    "workflow_timeline_style": {"Enterprise", "Subtle", "Frappe Standard"},
    "state_presentation": {"Illustrated Minimal", "Compact", "Frappe Standard"},
    "workspace_layout_style": {"Enterprise Canvas", "Compact Operations", "Frappe Standard"},
    "kpi_card_style": {"Executive", "Operational", "Frappe Standard"},
    "chart_presentation": {"Balanced", "High Contrast", "Frappe Standard"},
    "priority_panel_style": {"Action Oriented", "Compact", "Frappe Standard"},
    "activity_panel_style": {"Timeline Cards", "Compact Feed", "Frappe Standard"},
    "operational_table_style": {"Enterprise", "Compact Operations", "Frappe Standard"},
    "login_experience_style": {"QOrg Executive", "QOrg Midnight", "QOrg Visual", "Frappe Standard"},
    "login_form_density": {"Comfortable", "Compact", "Frappe Standard"},
    "login_card_alignment": {"Auto", "Start", "Center", "End"},
    "web_form_presentation": {"Enterprise", "Compact", "Frappe Standard"},
    "portal_presentation": {"Enterprise", "Compact", "Frappe Standard"},
    "public_card_style": {"Elevated", "Subtle", "Frappe Standard"},
    "public_success_presentation": {"Celebratory Minimal", "Compact", "Frappe Standard"},
}
COLOR_FIELDS = (
    "primary_accent", "secondary_accent", "neutral_accent", "success_color",
    "warning_color", "danger_color", "information_color", "focus_color",
    "navbar_surface", "sidebar_surface", "page_surface", "card_surface",
    "dialog_surface", "input_surface", "text_primary_color", "text_muted_color",
    "heading_color", "border_color", "selected_surface", "hover_surface",
)
VISUAL_FIELDS = tuple(ENUMS) + COLOR_FIELDS + (
    'body_font_size',
    'label_font_size',
    'heading_scale',
    'navbar_height',
    'sidebar_width',
    'page_header_height',
    'icon_size',
    'enhanced_section_headings',
    'compact_child_tables',
    'sticky_list_header',
    'reduced_transparency',
    'respect_reduced_motion',
    'enhanced_focus_visibility',
    'rtl_spacing_corrections',
    'sticky_primary_columns',
    'numeric_alignment',
    'workspace_quick_actions',
    'dashboard_responsive_reflow',
    'dashboard_reduce_decorative_motion',
    'login_show_trust_message',
    'login_trust_message',
    'login_show_security_footer',
    'login_focus_first_field',
    'public_validation_summary',
    'public_mobile_sticky_actions',
    'login_visual_gradient',
    'login_welcome_title',
    'login_welcome_subtitle',
    'web_form_max_content_width',
    'web_form_sticky_actions',
    'web_form_hide_technical_child_row_name',
    'action_dock_tooltips',
    'show_create_action',
    'show_language_action',
    'create_menu_search',
    'group_create_items',
)
CONFIG_FIELDS = VISUAL_FIELDS + (
    'enabled',
    'apply_to_desk',
    'apply_to_login',
    'apply_to_qorg_web_components',
    'respect_active_website_theme',
    'active_preset',
    'login_visual_image',
    'show_login_language_switcher',
    'enable_quick_create_menu',
    'quick_create_button_label',
    'enable_action_dock',
)
DEFAULTS = {
    "primary_accent": "#137690",
    "secondary_accent": "#cbae66",
    "neutral_accent": "#606c77",
    "success_color": "#2e8b57",
    "warning_color": "#d79b26",
    "danger_color": "#bd4546",
    "information_color": "#258bd3",
    "focus_color": "#269ad7",
    "navbar_surface": "#fafafa",
    "sidebar_surface": "#f2f6f7",
    "page_surface": "#f6f8fa",
    "card_surface": "#ffffff",
    "dialog_surface": "#ffffff",
    "input_surface": "#ffffff",
    "text_primary_color": "#0f3246",
    "text_muted_color": "#606c77",
    "heading_color": "#0f3246",
    "border_color": "#d6e0e4",
    "selected_surface": "#e0f1f5",
    "hover_surface": "#edf7f9",
    "enabled": 0, "apply_to_desk": 1, "apply_to_login": 0,
    "apply_to_qorg_web_components": 1, "respect_active_website_theme": 1,
    "theme_mode_policy": "Light", "density": "Comfortable",
    "typography_policy": "System UI", "heading_weight": "Semibold",
    "line_height_scale": "Comfortable", "control_radius": "Compact",
    "button_radius": "Compact", "card_radius": "Compact",
    "dialog_radius": "Compact", "border_strength": "Subtle",
    "elevation_scale": "Subtle", "workspace_card_density": "Comfortable",
    "dialog_width_policy": "Adaptive", "status_indicator_strength": "Enhanced",
    "respect_reduced_motion": 1, "enhanced_focus_visibility": 1,
    "contrast_policy": "WCAG AA Guard", "rtl_spacing_corrections": 1,
    "touch_target_policy": "Enhanced", "login_layout": "QOrg Split",
    "login_visual_source": "Gradient", "login_visual_gradient": "QOrg Blue",
    "login_welcome_title": "Welcome to QOrg", "login_welcome_subtitle": "Integrated, secure and efficient enterprise management.", "login_mobile_visual_policy": "Hide",
    "show_login_language_switcher": 1, "web_form_max_content_width": 1180,
    "web_form_hide_technical_child_row_name": 1, "web_form_sticky_actions": 1, "body_font_size": 13,
    "label_font_size": 13, "heading_scale": 1.2, "navbar_height": 50, "page_header_height": 50,
    "sidebar_width": 240, "icon_size": 16, "enable_quick_create_menu": 1,
    "quick_create_button_label": "Create",
    "experience_style": "QOrg Executive", "surface_hierarchy": "Layered",
    "navigation_emphasis": "Balanced", "page_header_style": "Executive",
    "section_presentation": "Structured", "table_presentation": "Enterprise",
    "enable_action_dock": 1, "action_dock_desktop_placement": "Auto",
    "action_dock_mobile_placement": "Floating Orb",
    "action_dock_collapsed_behavior": "Expand on Hover",
    "show_create_action": 1, "show_language_action": 1,
    "create_menu_search": 1, "group_create_items": 1,
    "action_dock_tooltips": 1,
    "form_control_style": "Enterprise", "toolbar_style": "Unified",
    "grid_style": "Enterprise", "alternate_view_style": "Enterprise",
    "dialog_style": "Enterprise", "workflow_timeline_style": "Enterprise",
    "state_presentation": "Illustrated Minimal", "sticky_primary_columns": 1,
    "numeric_alignment": 1,
    "workspace_layout_style": "Enterprise Canvas", "kpi_card_style": "Executive",
    "chart_presentation": "Balanced", "priority_panel_style": "Action Oriented",
    "activity_panel_style": "Timeline Cards", "operational_table_style": "Enterprise",
    "workspace_quick_actions": 1, "dashboard_responsive_reflow": 1,
    "dashboard_reduce_decorative_motion": 1,
    "login_experience_style": "QOrg Executive", "login_form_density": "Comfortable",
    "login_show_trust_message": 1, "login_trust_message": "Secure access to your organization workspace.",
    "login_card_alignment": "Auto", "login_show_security_footer": 1, "login_focus_first_field": 1,
    "web_form_presentation": "Enterprise", "portal_presentation": "Enterprise",
    "public_card_style": "Elevated", "public_validation_summary": 1,
    "public_success_presentation": "Celebratory Minimal", "public_mobile_sticky_actions": 1,
}


def _hex(value: str | None) -> str | None:
    if not value:
        return None
    value = str(value).strip().lower()
    if not (value.startswith("#") and len(value) in (4, 7)):
        frappe.throw(_("Invalid hexadecimal color: {0}").format(value))
    try:
        int(value[1:], 16)
    except ValueError:
        frappe.throw(_("Invalid hexadecimal color: {0}").format(value))
    return value


def _rgb(value: str) -> tuple[float, float, float]:
    value = value.lstrip("#")
    if len(value) == 3:
        value = "".join(char * 2 for char in value)
    return tuple(int(value[index : index + 2], 16) / 255 for index in (0, 2, 4))


def _luminance(value: str) -> float:
    channels = []
    for channel in _rgb(value):
        channels.append(channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def _contrast(first: str, second: str) -> float:
    brighter, darker = sorted((_luminance(first), _luminance(second)), reverse=True)
    return (brighter + 0.05) / (darker + 0.05)


def _best_foreground(background: str) -> str:
    return "#ffffff" if _contrast(background, "#ffffff") >= _contrast(background, "#111827") else "#111827"


def validate_values(doc) -> None:
    for fieldname, allowed in ENUMS.items():
        if doc.meta.has_field(fieldname) and doc.get(fieldname) and doc.get(fieldname) not in allowed:
            frappe.throw(_("Invalid value for {0}: {1}").format(fieldname, doc.get(fieldname)))
    for fieldname in COLOR_FIELDS:
        if doc.meta.has_field(fieldname):
            doc.set(fieldname, _hex(doc.get(fieldname)))

    limits = {
        "web_form_max_content_width": (760, 1600, 1180),
        "body_font_size": (12, 20, 14), "label_font_size": (11, 18, 13),
        "navbar_height": (40, 72, 48), "sidebar_width": (200, 340, 240),
        "icon_size": (14, 24, 16), "page_header_height": (40, 72, 50),
    }
    for fieldname, (minimum, maximum, fallback) in limits.items():
        if doc.meta.has_field(fieldname):
            value = cint(doc.get(fieldname) if doc.get(fieldname) is not None else fallback)
            if value < minimum or value > maximum:
                frappe.throw(_("{0} must be between {1} and {2}.").format(fieldname, minimum, maximum))
            doc.set(fieldname, value)
    if doc.meta.has_field("heading_scale"):
        scale = float(doc.get("heading_scale") or 1.2)
        if scale < 1.0 or scale > 1.6:
            frappe.throw(_("Heading scale must be between 1.0 and 1.6."))
        doc.heading_scale = scale

    if doc.get("contrast_policy") == "WCAG AA Guard":
        for text_field, surface_field, label in (
            ("text_primary_color", "page_surface", _("page")),
            ("text_primary_color", "card_surface", _("card")),
            ("text_primary_color", "input_surface", _("input")),
            ("heading_color", "page_surface", _("page heading")),
        ):
            text, surface = doc.get(text_field), doc.get(surface_field)
            if text and surface and _contrast(text, surface) < 4.5:
                frappe.throw(_("The {0} colors do not meet the configured WCAG AA contrast guard.").format(label))

    if doc.doctype == SETTINGS:
        if doc.get("enabled") and not any(doc.get(fieldname) for fieldname in ("apply_to_desk", "apply_to_login", "apply_to_qorg_web_components")):
            frappe.throw(_("Select at least one application scope."))
        seen = set()
        for row in doc.get("quick_create_items") or []:
            if not row.reference_doctype:
                continue
            if row.reference_doctype in seen:
                frappe.throw(_("Document Type {0} is repeated in the Create menu.").format(row.reference_doctype))
            seen.add(row.reference_doctype)
            meta = frappe.get_meta(row.reference_doctype)
            if meta.istable or meta.issingle:
                frappe.throw(_("{0} cannot be used in the Create menu because it is a child or single document type.").format(row.reference_doctype))
            row.sequence = cint(row.sequence if row.sequence is not None else 10)
            if row.sequence < 0 or row.sequence > 9999:
                frappe.throw(_("Create menu sequence must be between 0 and 9999."))
            if row.display_label and len(row.display_label) > 140:
                frappe.throw(_("Create menu labels cannot exceed 140 characters."))
            if row.icon and not re.fullmatch(r"[a-z0-9-]{1,64}", row.icon):
                frappe.throw(_("Create menu icon names may contain lowercase letters, numbers and hyphens only."))
            if row.menu_group and len(row.menu_group) > 80:
                frappe.throw(_("Create menu group names cannot exceed 80 characters."))
            if row.description and len(row.description) > 240:
                frappe.throw(_("Create menu descriptions cannot exceed 240 characters."))
        if doc.get("quick_create_button_label") and len(doc.quick_create_button_label) > 40:
            frappe.throw(_("The Create button label cannot exceed 40 characters."))
        doc.configuration_status = "Valid"
        doc.compatibility_status = "Validated baseline: Frappe 16.53+"
        if doc.meta.has_field("active_website_theme"):
            doc.active_website_theme = frappe.db.get_single_value("Website Settings", "website_theme") or "Frappe Standard"
        if doc.meta.has_field("website_integration_status"):
            doc.website_integration_status = "Website Theme respected" if doc.get("respect_active_website_theme") else "QOrg managed tokens"


def values_from(doc, *, with_defaults: bool = True) -> dict[str, Any]:
    values = dict(DEFAULTS) if with_defaults else {}
    for fieldname in CONFIG_FIELDS:
        if doc.meta.has_field(fieldname) and doc.get(fieldname) not in (None, ""):
            values[fieldname] = doc.get(fieldname)
    return values


def preset_values(name: str | None) -> dict[str, Any]:
    if not name or not frappe.db.exists(PRESET, name):
        return {}
    return values_from(frappe.get_doc(PRESET, name), with_defaults=False)


def effective(use_cache: bool = True) -> dict[str, Any]:
    if use_cache:
        cached = frappe.cache().get_value(CACHE_KEY)
        if cached:
            return cached if isinstance(cached, dict) else json.loads(cached)
    if not frappe.db.exists("DocType", SETTINGS):
        return {**DEFAULTS, "css_variables": {}}
    doc = frappe.get_single(SETTINGS)
    values = {**DEFAULTS, **preset_values(doc.active_preset), **values_from(doc, with_defaults=False)}
    values["schema_version"] = DESIGN_SYSTEM_SCHEMA_VERSION
    values["css_variables"] = css_variables(values)
    values["fingerprint"] = fingerprint(values)
    frappe.cache().set_value(CACHE_KEY, values, expires_in_sec=3600)
    return values


def css_variables(values: dict[str, Any]) -> dict[str, str]:
    variables: dict[str, str] = {}
    mapping = {
        "primary_accent": "--qorg-accent-primary", "secondary_accent": "--qorg-accent-secondary",
        "neutral_accent": "--qorg-accent-neutral", "success_color": "--qorg-status-success",
        "warning_color": "--qorg-status-warning", "danger_color": "--qorg-status-danger",
        "information_color": "--qorg-status-info", "focus_color": "--qorg-focus-color",
        "navbar_surface": "--qorg-navbar-surface", "sidebar_surface": "--qorg-sidebar-surface",
        "page_surface": "--qorg-page-surface", "card_surface": "--qorg-card-surface",
        "dialog_surface": "--qorg-dialog-surface", "input_surface": "--qorg-input-surface",
        "text_primary_color": "--qorg-text-primary", "text_muted_color": "--qorg-text-muted",
        "heading_color": "--qorg-heading-color", "border_color": "--qorg-border-color",
        "selected_surface": "--qorg-selected-surface", "hover_surface": "--qorg-hover-surface",
    }
    for fieldname, variable in mapping.items():
        if values.get(fieldname):
            variables[variable] = values[fieldname]

    radius = {"Frappe Default": "var(--border-radius,6px)", "Compact": "4px", "Subtle": "8px", "Rounded": "14px"}
    for fieldname, variable in (("control_radius", "--qorg-control-radius"), ("button_radius", "--qorg-button-radius"), ("card_radius", "--qorg-card-radius"), ("dialog_radius", "--qorg-dialog-radius")):
        variables[variable] = radius.get(values.get(fieldname), radius["Frappe Default"])

    density = {
        "Frappe Default": ("var(--input-height,34px)", "var(--padding-sm,8px)", "var(--list-row-height,40px)"),
        "Comfortable": ("42px", "10px", "48px"), "Compact": ("32px", "6px", "36px"),
    }[values.get("density", "Frappe Default")]
    variables["--qorg-control-height"], variables["--qorg-component-padding"], variables["--qorg-row-height"] = density
    variables["--qorg-body-font-size"] = f"{cint(values.get('body_font_size') or 14)}px"
    variables["--qorg-label-font-size"] = f"{cint(values.get('label_font_size') or 13)}px"
    variables["--qorg-heading-scale"] = str(values.get("heading_scale") or 1.2)
    variables["--qorg-navbar-height"] = f"{cint(values.get('navbar_height') or 50)}px"
    variables["--qorg-page-head-height"] = f"{cint(values.get('page_header_height') or 50)}px"
    variables["--qorg-sidebar-width"] = f"{cint(values.get('sidebar_width') or 240)}px"
    variables["--qorg-icon-size"] = f"{cint(values.get('icon_size') or 16)}px"
    variables["--qorg-web-form-max-width"] = f"{cint(values.get('web_form_max_content_width') or 1180)}px"
    variables["--qorg-heading-weight"] = {"Default": "var(--weight-semibold,600)", "Medium": "500", "Semibold": "600"}.get(values.get("heading_weight"), "600")
    variables["--qorg-line-height"] = {"Default": "var(--line-height-base,1.5)", "Comfortable": "1.6", "Spacious": "1.75"}.get(values.get("line_height_scale"), "1.5")
    variables["--qorg-font-family"] = {"Frappe Default": "inherit", "System UI": "system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif", "QOrg Bundled": "var(--font-stack,system-ui,sans-serif)"}.get(values.get("typography_policy"), "inherit")
    variables["--qorg-border-width"] = {"Frappe Default": "1px", "Subtle": "1px", "Defined": "2px"}.get(values.get("border_strength"), "1px")
    variables["--qorg-elevation"] = {"Frappe Default": "var(--shadow-sm,0 1px 2px rgba(0,0,0,.08))", "Flat": "none", "Subtle": "0 4px 16px rgba(15,23,42,.08)", "Elevated": "0 12px 32px rgba(15,23,42,.14)"}.get(values.get("elevation_scale"), "none")
    variables["--qorg-workspace-card-padding"] = {"Frappe Default": "var(--padding-md,12px)", "Comfortable": "16px", "Compact": "10px"}.get(values.get("workspace_card_density"), "12px")
    variables["--qorg-dialog-max-width"] = "min(92vw,1100px)" if values.get("dialog_width_policy") == "Adaptive" else "none"
    variables["--qorg-status-opacity"] = "1" if values.get("status_indicator_strength") == "Enhanced" else ".88"
    variables["--qorg-touch-target"] = "44px" if values.get("touch_target_policy") == "Enhanced" else "var(--control-height,34px)"
    if values.get("primary_accent"):
        variables["--qorg-accent-foreground"] = _best_foreground(values["primary_accent"])
    # Enterprise Experience semantic levels. Values inherit configured colors
    # while retaining safe fallbacks for Frappe light and dark modes.
    variables["--qorg-app-bg"] = values.get("page_surface") or "#f3f6f8"
    variables["--qorg-page-bg"] = values.get("page_surface") or "#f8fafb"
    variables["--qorg-surface"] = values.get("card_surface") or "#ffffff"
    variables["--qorg-surface-raised"] = values.get("dialog_surface") or "#ffffff"
    variables["--qorg-surface-subtle"] = values.get("sidebar_surface") or "#eef3f5"
    variables["--qorg-border-subtle"] = values.get("border_color") or "#e1e8eb"
    variables["--qorg-text-strong"] = values.get("heading_color") or "#0f2735"
    variables["--qorg-brand-soft"] = values.get("selected_surface") or "#e0f1f5"
    variables["--qorg-hover-surface"] = values.get("hover_surface") or "#edf7f9"
    return variables


def fingerprint(values: dict[str, Any]) -> str:
    raw = json.dumps({key: value for key, value in values.items() if key != "fingerprint"}, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


def clear_cache() -> None:
    frappe.cache().delete_value(CACHE_KEY)


def sync_feature_control(enabled: bool) -> None:
    if not frappe.db.exists("DocType", "Feature Control Center"):
        return
    from qorg.qorg.enterprise_foundation.features import normalize_site_feature_rows

    center = frappe.get_single("Feature Control Center")
    normalize_site_feature_rows(center)
    for row in center.get("site_features") or []:
        if row.feature_key == "design_system":
            row.feature_state = "Enabled" if enabled else "Disabled"
            row.operating_mode = "Extensions" if enabled else "Standard Only"
            row.enabled = 1 if enabled else 0
            center.flags.ignore_permissions = True
            center.save()
            return


def update_state(status: str = "Managed") -> None:
    if not frappe.db.exists("DocType", "Managed Configuration State"):
        return
    config = effective(False)
    name = frappe.db.exists("Managed Configuration State", {"component_key": "qorg.design_system"})
    doc = frappe.get_doc("Managed Configuration State", name) if name else frappe.new_doc("Managed Configuration State")
    doc.update({
        "component_key": "qorg.design_system", "component_type": "Design System",
        "managed_version": DESIGN_SYSTEM_SCHEMA_VERSION, "management_status": status,
        "applied_fingerprint": config["fingerprint"], "last_seen_fingerprint": config["fingerprint"],
        "last_checked_on": now(), "details": json.dumps({
            "schema_version": DESIGN_SYSTEM_SCHEMA_VERSION, "active_preset": config.get("active_preset"),
            "scopes": {"desk": bool(config.get("apply_to_desk")), "login": bool(config.get("apply_to_login")), "web": bool(config.get("apply_to_qorg_web_components"))},
        }, sort_keys=True),
    })
    doc.flags.ignore_permissions = True
    doc.save()
