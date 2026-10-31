from __future__ import annotations
import frappe
from qorg.qorg.design_system.provisioning import provision_design_system
from qorg.qorg.design_system.service import SETTINGS, clear_cache

LEGACY_MAP={
 "theme_mode":"theme_mode_policy", "primary_color":"primary_accent", "accent_color":"secondary_accent",
 "login_image":"login_visual_image", "login_title":"login_welcome_title", "login_subtitle":"login_welcome_subtitle",
 "apply_to_web_forms":"apply_to_qorg_web_components", "show_create_action":"show_create_action", "show_language_action":"show_language_action",
}

def migrate_clean_theme():
    if not frappe.db.exists("DocType",SETTINGS): return
    settings=frappe.get_single(SETTINGS); changed=False
    for target,legacy in LEGACY_MAP.items():
        if settings.meta.has_field(target) and settings.meta.has_field(legacy) and settings.get(target) in (None,"") and settings.get(legacy) not in (None,""):
            settings.set(target,settings.get(legacy)); changed=True
    legacy_preset=settings.get("active_preset")
    aliases={"QOrg Executive Light":"Q Org Enterprise","QOrg Comfortable":"Q Org Enterprise","QOrg Midnight":"Q Org Dark","QOrg Compact Operations":"Q Org Compact","QOrg High Contrast":"Q Org Accessible"}
    if legacy_preset in aliases: settings.active_preset=aliases[legacy_preset]; changed=True
    if changed:
        settings.flags.ignore_permissions=True; settings.save()
    provision_design_system(); clear_cache()
