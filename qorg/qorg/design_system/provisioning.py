import frappe

from qorg.qorg.design_system.service import SETTINGS

DEFAULTS = {
    "primary_color": "#137690", "secondary_color": "#CBAE66", "border_radius": 4,
    "large_border_radius": 8, "page_background_color": "#FFFFFF", "surface_color": "#FFFFFF",
    "control_background_color": "#F4F5F6", "primary_text_color": "#1F272E",
    "muted_text_color": "#687178", "border_color": "#DFE2E5", "font_source": "Frappe Default",
    "font_weights": "400,500,600,700", "fallback_font_family": 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    "font_size_xs": 11, "font_size_sm": 12, "font_size_base": 14, "font_size_lg": 16,
    "font_size_h6": 14, "font_size_h5": 16, "font_size_h4": 18, "font_size_h3": 20,
    "font_size_h2": 24, "font_size_h1": 32, "font_size_display": 48,
    "body_line_height": 1.35, "paragraph_line_height": 1.55, "heading_line_height": 1.25,
    "show_language_action": 1, "enable_login_experience": 1, "show_login_language_switcher": 1,
    "login_background_position": "Center", "login_overlay_strength": "Medium", "login_text_color": "Light",
    "login_visual_title": "Q Org", "login_visual_subtitle": "Integrated enterprise management for your organization.",
    "login_form_title": "Welcome", "login_form_subtitle": "Sign in to continue",
    "login_image_panel_width": 48, "login_slide_interval": 6, "login_return_label": "Back to website",
    "login_return_url": "/",
}


def provision_login_experience():
    if not frappe.db.exists("DocType", SETTINGS):
        return
    doc = frappe.get_single(SETTINGS)
    changed = False
    for fieldname, value in DEFAULTS.items():
        if doc.meta.has_field(fieldname) and doc.get(fieldname) in (None, ""):
            doc.set(fieldname, value)
            changed = True
    if changed:
        doc.flags.ignore_permissions = True
        doc.save()
    frappe.clear_cache()


def provision_theme_tokens():
    if not frappe.db.exists("DocType", SETTINGS):
        return
    doc = frappe.get_single(SETTINGS)
    changed = False
    for field in doc.meta.fields:
        if field.default in (None, "") or doc.get(field.fieldname) not in (None, ""):
            continue
        if field.fieldtype in ("Color", "Int", "Float", "Data", "Select", "Check"):
            doc.set(field.fieldname, field.default)
            changed = True
    if changed:
        doc.flags.ignore_permissions = True
        doc.save()
    frappe.clear_cache()
