import frappe

from qorg.qorg.design_system import LOGIN_EXPERIENCE_VERSION
from qorg.qorg.design_system.service import (
    SETTINGS,
    THEME_COLOR_PREFIXES,
    THEME_SIZE_FIELDS,
    get_login_configuration,
    get_theme_configuration,
    get_ui_tokens,
)


def audit_login_experience():
    config = get_login_configuration()
    tokens = get_ui_tokens(getattr(frappe.local, "lang", None))
    required = ("primary_color", "border_radius", "font_size_base", "font_size_h1")
    issues = [f"Missing token: {name}" for name in required if tokens.get(name) in (None, "")]
    if len(config.get("slides") or []) > 6:
        issues.append("More than six enabled login slides were returned.")
    return {
        "valid": not issues,
        "version": LOGIN_EXPERIENCE_VERSION,
        "site": frappe.local.site,
        "issues": issues,
        "slide_count": len(config.get("slides") or []),
        "font_external": bool(config.get("font_stylesheet_url")),
    }


def audit_theme_configuration():
    doc = frappe.get_single(SETTINGS)
    config = get_theme_configuration()
    colors = config.get("colors") or {}
    sizes = config.get("sizes") or {}
    issues = []

    expected_colors = [
        field.fieldname
        for field in doc.meta.fields
        if field.fieldtype == "Color" and field.fieldname.startswith(THEME_COLOR_PREFIXES)
    ]
    for name in expected_colors:
        if name not in colors:
            issues.append(f"Missing color token: {name}")

    for name in THEME_SIZE_FIELDS:
        if doc.meta.has_field(name) and name not in sizes:
            issues.append(f"Missing size token: {name}")

    zero_safe_fields = (
        "default_field_radius", "default_button_radius", "default_card_radius", "default_menu_radius",
        "desk_field_radius", "desk_button_radius", "desk_card_radius",
        "web_field_radius", "web_button_radius", "web_card_radius",
        "sidebar_item_radius", "sidebar_item_padding", "menu_radius", "menu_item_radius",
        "menu_item_padding", "workspace_widget_radius", "workspace_widget_hover_lift",
    )
    zero_values = {
        name: sizes.get(name)
        for name in zero_safe_fields
        if doc.meta.has_field(name) and int(doc.get(name) or 0) == 0
    }
    for name, value in zero_values.items():
        if value != 0:
            issues.append(f"Zero value was not preserved: {name} -> {value}")

    return {
        "valid": not issues,
        "site": frappe.local.site,
        "issues": issues,
        "color_count": len(colors),
        "size_count": len(sizes),
        "zero_values": zero_values,
        "primary_color": config.get("primary_color"),
        "secondary_color": config.get("secondary_color"),
    }
