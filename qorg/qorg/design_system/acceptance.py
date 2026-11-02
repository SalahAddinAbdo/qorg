import frappe

from qorg.qorg.design_system import LOGIN_EXPERIENCE_VERSION
from qorg.qorg.design_system.service import SETTINGS, get_login_configuration, get_ui_tokens


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


def audit_design_system_settings():
    from qorg.qorg.design_system.service import THEME_COLOR_PREFIXES, THEME_SIZE_FIELDS, get_theme_configuration

    doc = frappe.get_single(SETTINGS)
    theme = get_theme_configuration()
    issues = []

    expected_colors = [
        field.fieldname
        for field in doc.meta.fields
        if field.fieldtype == "Color" and field.fieldname.startswith(THEME_COLOR_PREFIXES)
    ]
    for name in expected_colors:
        if name not in (theme.get("colors") or {}):
            issues.append(f"Missing color token: {name}")

    for name in THEME_SIZE_FIELDS:
        if doc.meta.has_field(name) and name not in (theme.get("sizes") or {}):
            issues.append(f"Missing size token: {name}")
        elif doc.meta.has_field(name) and doc.get(name) == 0 and theme["sizes"].get(name) != 0:
            issues.append(f"Zero value was not preserved: {name}")

    return {
        "valid": not issues,
        "issues": issues,
        "color_count": len(theme.get("colors") or {}),
        "size_count": len(theme.get("sizes") or {}),
        "show_language_action": bool(doc.show_language_action),
        "quick_create_rows": len(doc.quick_create_items or []),
    }
