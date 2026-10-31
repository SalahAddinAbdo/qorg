import frappe
from qorg.qorg.design_system import DESIGN_SYSTEM_SCHEMA_VERSION

PALETTE = {'primary_accent': '#137690', 'secondary_accent': '#cbae66', 'neutral_accent': '#606c77', 'success_color': '#2e8b57', 'warning_color': '#d79b26', 'danger_color': '#bd4546', 'information_color': '#258bd3', 'focus_color': '#269ad7', 'navbar_surface': '#fafafa', 'sidebar_surface': '#f2f6f7', 'page_surface': '#f6f8fa', 'card_surface': '#ffffff', 'dialog_surface': '#ffffff', 'input_surface': '#ffffff', 'text_primary_color': '#0f3246', 'text_muted_color': '#606c77', 'heading_color': '#0f3246', 'border_color': '#d6e0e4', 'selected_surface': '#e0f1f5', 'hover_surface': '#edf7f9'}

TYPOGRAPHY_V29 = {
    "font_source": "System and Frappe",
    "language_font_strategy": "Automatic Best Match",
    "latin_font_family": "Inter",
    "arabic_font_family": "Noto Sans Arabic",
    "typography_weight_system": "Balanced",
    "custom_font_stack": "system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif",
    "prefer_locally_hosted_fonts": 0,
}

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
    "QOrg Comfortable": {
        **TYPOGRAPHY_V29,
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
    "QOrg Compact": {
        **TYPOGRAPHY_V29,
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


# Complete enterprise preset gallery. Existing compatible records are adopted
# without overwriting user-managed changes.
PRESETS.update({
    "QOrg Executive Light": {
        **TYPOGRAPHY_V29,
        "theme_mode_policy": "Light", "density": "Comfortable", "experience_style": "QOrg Executive",
        "surface_hierarchy": "Layered", "navigation_emphasis": "Balanced", "page_header_style": "Executive",
        "form_control_style": "Enterprise", "toolbar_style": "Unified", "grid_style": "Enterprise",
        "workspace_layout_style": "Enterprise Canvas", "kpi_card_style": "Executive", "chart_presentation": "Balanced",
        "login_experience_style": "QOrg Executive", "web_form_presentation": "Enterprise", "portal_presentation": "Enterprise",
        **PALETTE,
    },
    "QOrg Midnight": {
        **TYPOGRAPHY_V29,
        "theme_mode_policy": "Dark", "density": "Comfortable", "experience_style": "QOrg Midnight",
        "surface_hierarchy": "Layered", "navigation_emphasis": "Brand Forward", "page_header_style": "Executive",
        "form_control_style": "Enterprise", "toolbar_style": "Unified", "grid_style": "Enterprise",
        "workspace_layout_style": "Enterprise Canvas", "kpi_card_style": "Executive", "chart_presentation": "High Contrast",
        "login_experience_style": "QOrg Midnight", "web_form_presentation": "Enterprise", "portal_presentation": "Enterprise",
        **PALETTE,
        "navbar_surface": "#0b1b24", "sidebar_surface": "#0f252f", "page_surface": "#091820",
        "card_surface": "#122832", "dialog_surface": "#122832", "input_surface": "#10242d",
        "text_primary_color": "#e7f2f5", "text_muted_color": "#9db0b8", "heading_color": "#f4f8f9",
        "border_color": "#29434f", "selected_surface": "#173b49", "hover_surface": "#14313d",
    },
    "QOrg Compact Operations": {
        **TYPOGRAPHY_V29,
        "theme_mode_policy": "Follow Frappe/System", "density": "Compact", "experience_style": "QOrg Operations",
        "surface_hierarchy": "Subtle", "navigation_emphasis": "Minimal", "form_control_style": "Compact Operations",
        "toolbar_style": "Compact", "grid_style": "Compact Operations", "dialog_style": "Compact",
        "workspace_layout_style": "Compact Operations", "kpi_card_style": "Operational",
        "priority_panel_style": "Compact", "activity_panel_style": "Compact Feed",
        "operational_table_style": "Compact Operations", "login_form_density": "Compact",
        "web_form_presentation": "Compact", "portal_presentation": "Compact", **PALETTE,
    },
    "QOrg High Contrast": {
        **TYPOGRAPHY_V29,
        "theme_mode_policy": "Follow Frappe/System", "density": "Comfortable", "contrast_policy": "WCAG AA Guard",
        "enhanced_focus_visibility": 1, "touch_target_policy": "Enhanced", "chart_presentation": "High Contrast",
        "border_strength": "Defined", "status_indicator_strength": "Enhanced", "primary_accent": "#006f86",
        "secondary_accent": "#8a6818", "neutral_accent": "#45535e", "success_color": "#147548",
        "warning_color": "#9b6400", "danger_color": "#a3282e", "information_color": "#0b6fa4",
        "focus_color": "#005fcc", "navbar_surface": "#ffffff", "sidebar_surface": "#f3f6f7",
        "page_surface": "#f8fafb", "card_surface": "#ffffff", "dialog_surface": "#ffffff",
        "input_surface": "#ffffff", "text_primary_color": "#092433", "text_muted_color": "#44545f",
        "heading_color": "#061d29", "border_color": "#9aabb4", "selected_surface": "#d9eef3",
        "hover_surface": "#e8f4f6",
    },
})

def provision_design_system():
    if not frappe.db.exists("DocType", "Q Org Design Preset"):
        return
    for name, values in PRESETS.items():
        if frappe.db.exists("Q Org Design Preset", name):
            continue
        doc = frappe.get_doc({
            "doctype": "Q Org Design Preset", "preset_name": name,
            "description": f"Managed QOrg preset: {name}.", "enabled": 1,
            "is_standard": 1, "schema_version": DESIGN_SYSTEM_SCHEMA_VERSION, **values,
        })
        doc.flags.ignore_permissions = True
        doc.insert()
    settings = frappe.get_single("Q Org Design System Settings")
    changed = False
    defaults = {
        **PALETTE,
        **TYPOGRAPHY_V29,
        "active_preset": "QOrg Executive Light",
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
        "login_layout": "QOrg Split", "login_visual_source": "Gradient",
        "login_visual_gradient": "QOrg Blue", "login_welcome_title": "Welcome to QOrg",
        "login_welcome_subtitle": "Integrated, secure and efficient enterprise management.",
        "show_login_language_switcher": 1, "login_mobile_visual_policy": "Hide",
        "web_form_max_content_width": 1180, "web_form_sticky_actions": 1,
        "web_form_hide_technical_child_row_name": 1,
        "enable_quick_create_menu": 1, "quick_create_button_label": "Create",
        "experience_style": "QOrg Executive",
        "surface_hierarchy": "Layered", "navigation_emphasis": "Balanced",
        "page_header_style": "Executive", "section_presentation": "Structured",
        "table_presentation": "Enterprise", "enable_action_dock": 1,
        "action_dock_desktop_placement": "Auto",
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
        "login_layout": "Full Width Split", "login_mobile_visual_policy": "Compact Header",
        "login_experience_style": "QOrg Executive", "login_form_density": "Comfortable",
        "login_show_trust_message": 1, "login_trust_message": "Secure access to your organization workspace.",
        "login_card_alignment": "Auto", "login_show_security_footer": 1, "login_focus_first_field": 1,
        "web_form_presentation": "Enterprise", "portal_presentation": "Enterprise",
        "public_card_style": "Elevated", "public_validation_summary": 1,
        "public_success_presentation": "Celebratory Minimal", "public_mobile_sticky_actions": 1,
    }
    for fieldname, value in defaults.items():
        if settings.meta.has_field(fieldname) and settings.get(fieldname) in (None, ""):
            settings.set(fieldname, value)
            changed = True
    if settings.enabled is None:
        settings.enabled = 1
        changed = True
    if changed:
        settings.flags.ignore_permissions = True
        settings.save()
