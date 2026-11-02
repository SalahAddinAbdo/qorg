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
