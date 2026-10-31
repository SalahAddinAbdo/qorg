from __future__ import annotations

import frappe

SETTINGS = "Q Org Design System Settings"
PRESET = "Q Org Design Preset"
BASELINE_PRESET = "Frappe Standard"
LOGIN_FIELDS = (
    "enable_login_experience", "show_login_language_switcher",
    "login_background_image", "login_background_position",
    "login_overlay_strength", "login_text_color", "login_visual_title",
    "login_visual_subtitle", "login_form_title", "login_form_subtitle",
    "login_brand_logo", "login_footer_text",
)

def get_login_configuration():
    doc=frappe.get_single(SETTINGS)
    return {field: doc.get(field) for field in LOGIN_FIELDS if doc.meta.has_field(field)}
