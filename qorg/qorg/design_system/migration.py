import frappe

from qorg.qorg.design_system.provisioning import provision_login_experience
from qorg.qorg.design_system.service import SETTINGS


def migrate_login_experience():
    provision_login_experience()
    if not frappe.db.exists("DocType", SETTINGS):
        return
    doc = frappe.get_single(SETTINGS)
    if not doc.meta.has_field("login_slides") or doc.get("login_slides"):
        return
    if doc.meta.has_field("login_background_image") and doc.login_background_image:
        doc.append("login_slides", {
            "enabled": 1,
            "image": doc.login_background_image,
            "title": doc.get("login_visual_title"),
            "subtitle": doc.get("login_visual_subtitle"),
            "image_position": doc.get("login_background_position") or "Center",
            "overlay_opacity": 38,
            "text_alignment": "Center",
        })
        doc.flags.ignore_permissions = True
        doc.save()
    frappe.clear_cache()
