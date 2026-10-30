import frappe
from qorg.qorg.design_system import DESIGN_SYSTEM_SCHEMA_VERSION

PALETTE = {'primary_accent': '#137690', 'secondary_accent': '#cbae66', 'neutral_accent': '#606c77', 'success_color': '#2e8b57', 'warning_color': '#d79b26', 'danger_color': '#bd4546', 'information_color': '#258bd3', 'focus_color': '#269ad7', 'navbar_surface': '#fafafa', 'sidebar_surface': '#f2f6f7', 'page_surface': '#f6f8fa', 'card_surface': '#ffffff', 'dialog_surface': '#ffffff', 'input_surface': '#ffffff', 'text_primary_color': '#0f3246', 'text_muted_color': '#606c77', 'heading_color': '#0f3246', 'border_color': '#d6e0e4', 'selected_surface': '#e0f1f5', 'hover_surface': '#edf7f9'}

PRESETS = {
    "Frappe Standard": {
        "theme_mode_policy": "Follow Frappe/System", "density": "Frappe Default",
        "typography_policy": "Frappe Default", "heading_weight": "Default",
        "line_height_scale": "Default", "control_radius": "Frappe Default",
        "button_radius": "Frappe Default", "card_radius": "Frappe Default",
        "dialog_radius": "Frappe Default", "border_strength": "Frappe Default",
        "elevation_scale": "Frappe Default", "workspace_card_density": "Frappe Default",
        "dialog_width_policy": "Frappe Default", "status_indicator_strength": "Frappe Default",
        "touch_target_policy": "Frappe Default",
    },
    "Q Org Comfortable": {
        **PALETTE, "theme_mode_policy": "Light", "density": "Comfortable",
        "typography_policy": "System UI", "heading_weight": "Semibold",
        "line_height_scale": "Comfortable", "body_font_size": 13, "label_font_size": 13,
        "heading_scale": 1.2, "navbar_height": 50, "page_header_height": 50,
        "sidebar_width": 240, "icon_size": 16, "control_radius": "Compact",
        "button_radius": "Compact", "card_radius": "Compact", "dialog_radius": "Compact",
        "border_strength": "Subtle", "elevation_scale": "Subtle",
        "enhanced_section_headings": 1, "compact_child_tables": 0, "sticky_list_header": 1,
        "workspace_card_density": "Comfortable", "dialog_width_policy": "Adaptive",
        "status_indicator_strength": "Enhanced", "respect_reduced_motion": 1,
        "enhanced_focus_visibility": 1, "contrast_policy": "WCAG AA Guard",
        "rtl_spacing_corrections": 1, "touch_target_policy": "Enhanced",
    },
    "Q Org Compact": {
        **PALETTE, "theme_mode_policy": "Light", "density": "Compact",
        "typography_policy": "System UI", "heading_weight": "Semibold",
        "line_height_scale": "Default", "body_font_size": 13, "label_font_size": 12,
        "heading_scale": 1.16, "navbar_height": 50, "page_header_height": 50,
        "sidebar_width": 232, "icon_size": 16, "control_radius": "Compact",
        "button_radius": "Compact", "card_radius": "Compact", "dialog_radius": "Compact",
        "border_strength": "Subtle", "elevation_scale": "Flat",
        "enhanced_section_headings": 1, "compact_child_tables": 1, "sticky_list_header": 1,
        "workspace_card_density": "Compact", "dialog_width_policy": "Adaptive",
        "status_indicator_strength": "Enhanced", "respect_reduced_motion": 1,
        "enhanced_focus_visibility": 1, "contrast_policy": "WCAG AA Guard",
        "rtl_spacing_corrections": 1, "touch_target_policy": "Frappe Default",
    },
}

def provision_design_system():
    if not frappe.db.exists("DocType", "Q Org Design Preset"):
        return
    for name, values in PRESETS.items():
        if frappe.db.exists("Q Org Design Preset", name):
            continue
        doc = frappe.get_doc({
            "doctype": "Q Org Design Preset", "preset_name": name,
            "description": f"Managed Q Org preset: {name}.", "enabled": 1,
            "is_standard": 1, "schema_version": DESIGN_SYSTEM_SCHEMA_VERSION, **values,
        })
        doc.flags.ignore_permissions = True
        doc.insert()
    settings = frappe.get_single("Q Org Design System Settings")
    changed = False
    defaults = {
        **PALETTE,
        "active_preset": "Q Org Comfortable",
        "apply_to_desk": 1, "apply_to_login": 1,
        "apply_to_qorg_web_components": 1, "respect_active_website_theme": 1,
        "theme_mode_policy": "Light", "density": "Comfortable",
        "typography_policy": "System UI", "heading_weight": "Semibold",
        "line_height_scale": "Comfortable", "body_font_size": 13,
        "label_font_size": 13, "heading_scale": 1.2, "navbar_height": 50,
        "page_header_height": 50, "sidebar_width": 240, "icon_size": 16,
        "control_radius": "Compact", "button_radius": "Compact",
        "card_radius": "Compact", "dialog_radius": "Compact",
        "border_strength": "Subtle", "elevation_scale": "Subtle",
        "enhanced_section_headings": 1, "compact_child_tables": 0,
        "sticky_list_header": 1, "workspace_card_density": "Comfortable",
        "dialog_width_policy": "Adaptive", "status_indicator_strength": "Enhanced",
        "respect_reduced_motion": 1, "enhanced_focus_visibility": 1,
        "contrast_policy": "WCAG AA Guard", "rtl_spacing_corrections": 1,
        "touch_target_policy": "Enhanced", "reduced_transparency": 0,
        "login_layout": "Q Org Split", "login_visual_source": "Gradient",
        "login_visual_gradient": "Q Org Blue", "login_welcome_title": "Welcome to Q Org",
        "login_welcome_subtitle": "Integrated, secure and efficient enterprise management.",
        "show_login_language_switcher": 1, "login_mobile_visual_policy": "Hide",
        "web_form_max_content_width": 1180, "web_form_sticky_actions": 1,
        "web_form_hide_technical_child_row_name": 1,
        "enable_quick_create_menu": 1, "quick_create_button_label": "Create",
    }
    for fieldname, value in defaults.items():
        if settings.meta.has_field(fieldname) and settings.get(fieldname) in (None, ""):
            settings.set(fieldname, value)
            changed = True
    if settings.enabled is None:
        settings.enabled = 0
        changed = True
    if changed:
        settings.flags.ignore_permissions = True
        settings.save()
