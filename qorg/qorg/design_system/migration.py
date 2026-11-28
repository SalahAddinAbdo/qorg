import frappe

from qorg.qorg.design_system.provisioning import provision_login_experience, provision_theme_tokens
from qorg.qorg.design_system.service import SETTINGS


def migrate_login_experience():
    provision_login_experience()
    provision_theme_tokens()
    if not frappe.db.exists("DocType", SETTINGS):
        return
    doc = frappe.get_single(SETTINGS)
    changed = False
    legacy_map = {
        "page_background_color": ("desk_light_page_bg", "web_light_page_bg"),
        "surface_color": ("desk_light_surface_bg", "web_light_surface_bg"),
        "control_background_color": ("desk_light_control_bg", "web_light_control_bg"),
        "primary_text_color": ("desk_light_text", "web_light_text"),
        "muted_text_color": ("desk_light_muted_text", "web_light_muted_text"),
        "border_color": ("desk_light_border", "web_light_border"),
        "border_radius": ("desk_field_radius", "desk_button_radius", "web_field_radius", "web_button_radius"),
        "large_border_radius": ("desk_card_radius", "web_card_radius", "menu_radius"),
    }
    for source, targets in legacy_map.items():
        value = doc.get(source) if doc.meta.has_field(source) else None
        if value in (None, ""):
            continue
        for target in targets:
            if doc.meta.has_field(target) and doc.get(target) in (None, ""):
                doc.set(target, value)
                changed = True
    if doc.meta.has_field("login_slides") and not doc.get("login_slides") and doc.meta.has_field("login_background_image") and doc.login_background_image:
        doc.append("login_slides", {"enabled": 1, "image": doc.login_background_image, "title": doc.get("login_visual_title"), "subtitle": doc.get("login_visual_subtitle"), "image_position": doc.get("login_background_position") or "Center", "overlay_opacity": 38, "text_alignment": "Center"})
        changed = True
    if changed:
        doc.flags.ignore_permissions = True
        doc.save()
    frappe.clear_cache()


def migrate_legacy_web_form_design():
    """Bridge the historical v2.2 patch to the current managed Web Form services.

    The legacy patch path is part of ``patches.txt`` and must remain importable for
    clean installs and upgrades from databases where the patch has not run yet.
    Current provisioning and reconciliation services are idempotent and preserve
    user-managed Web Forms, so the bridge delegates to them instead of restoring
    obsolete migration logic.
    """
    from qorg.qorg.people_and_opportunities.web_form_policy import (
        reconcile_web_form_policy,
    )
    from qorg.qorg.people_and_opportunities.web_form_provisioning import (
        provision_standard_opportunity_web_forms,
    )

    provision_result = provision_standard_opportunity_web_forms()
    policy_result = reconcile_web_form_policy()
    frappe.clear_cache()
    return {
        "provisioning": provision_result,
        "policy": policy_result,
    }
