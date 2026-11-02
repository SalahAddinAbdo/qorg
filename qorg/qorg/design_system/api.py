import frappe
from frappe import _

from qorg.qorg.design_system.service import (
    get_font_stylesheet_url,
    get_login_configuration,
    get_theme_configuration,
    get_ui_tokens,
)


@frappe.whitelist(allow_guest=True)
def get_ui_configuration():
    config = get_ui_tokens(getattr(frappe.local, "lang", None))
    config["font_stylesheet_url"] = get_font_stylesheet_url()
    config["theme"] = get_theme_configuration()
    return config


@frappe.whitelist(allow_guest=True)
def get_login_experience():
    config = get_login_configuration()
    config["theme"] = get_theme_configuration()
    config["languages"] = frappe.get_all("Language", filters={"enabled": 1}, fields=["language_code", "language_name"], order_by="language_name")
    config["current_language"] = frappe.local.lang
    return config


@frappe.whitelist(methods=["POST"], allow_guest=True)
def set_login_language(language):
    if not frappe.db.exists("Language", {"language_code": language, "enabled": 1}):
        frappe.throw(_("Language is not enabled."))
    frappe.local.cookie_manager.set_cookie("preferred_language", language)
    return {"language": language}


@frappe.whitelist()
def get_available_languages():
    settings = frappe.get_single("Q Org Design System Settings")
    return {
        "current": frappe.local.lang,
        "show_language_action": bool(settings.show_language_action),
        "languages": frappe.get_all(
            "Language",
            filters={"enabled": 1},
            fields=["language_code", "language_name"],
            order_by="language_name",
        ),
    }


@frappe.whitelist(methods=["POST"])
def set_current_user_language(language):
    if not frappe.db.exists("Language", {"language_code": language, "enabled": 1}):
        frappe.throw(_("Language is not enabled."))
    frappe.db.set_value("User", frappe.session.user, "language", language)
    frappe.clear_cache(user=frappe.session.user)
    return {"language": language}


@frappe.whitelist()
def get_quick_create_menu():
    settings = frappe.get_single("Q Org Design System Settings")
    items = []
    seen = set()

    for row in settings.quick_create_items or []:
        doctype = row.reference_doctype
        if not row.enabled or not doctype or doctype in seen:
            continue
        if not frappe.db.exists("DocType", doctype):
            continue

        meta = frappe.get_meta(doctype)
        if meta.istable or meta.issingle or not frappe.has_permission(doctype, "create"):
            continue

        seen.add(doctype)
        items.append({
            "doctype": doctype,
            "label": row.display_label or frappe._(doctype),
            "group": row.menu_group or "Create",
            "description": row.description or "",
            "icon": row.icon or "add",
            "favorite": bool(row.is_favorite),
            "sequence": int(row.sequence or 10),
        })

    items.sort(key=lambda item: (not item["favorite"], item["sequence"], item["group"], item["label"]))
    return {"items": items}
