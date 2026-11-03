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
    config["user_theme_mode"] = _get_user_theme_mode()
    return config


def _get_user_theme_mode():
    if frappe.session.user == "Guest":
        return "Light"

    mode = frappe.db.get_value("User", frappe.session.user, "desk_theme") or "Light"
    return mode if mode in {"Light", "Dark", "Automatic"} else "Light"


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


def _is_page_permitted(page_name):
    try:
        page = frappe.get_doc("Page", page_name)
        checker = getattr(page, "is_permitted", None)
        if callable(checker):
            return bool(checker())
        return bool(frappe.has_permission("Page", "read", doc=page))
    except (frappe.DoesNotExistError, frappe.PermissionError):
        return False


def _get_permitted_report(report_name):
    try:
        from frappe.desk.query_report import get_report_doc

        return get_report_doc(report_name)
    except (frappe.DoesNotExistError, frappe.PermissionError, frappe.ValidationError):
        return None


@frappe.whitelist()
def get_open_menu():
    settings = frappe.get_single("Q Org Design System Settings")
    items = []
    seen = set()

    for row in settings.open_items or []:
        if not row.enabled or not row.resource_type:
            continue

        item = _build_open_item(row)
        if not item:
            continue

        key = (item["resource_type"], item["reference"])
        if key in seen:
            continue
        seen.add(key)
        items.append(item)

    items.sort(
        key=lambda item: (
            not item["favorite"],
            item["sequence"],
            item["group"],
            item["label"],
        )
    )
    return {"items": items}


def _build_open_item(row):
    resource_type = row.resource_type

    if resource_type == "Page":
        reference = row.page
        if not reference or not _is_page_permitted(reference):
            return None
        label = row.display_label or frappe.db.get_value("Page", reference, "title") or reference
        return _open_item_payload(row, reference, label, "page", "folder-open")

    if resource_type == "Report":
        reference = row.report
        report = _get_permitted_report(reference) if reference else None
        if not report:
            return None
        label = row.display_label or report.report_name or report.name
        payload = _open_item_payload(row, reference, label, "report", "chart")
        payload["ref_doctype"] = report.ref_doctype
        payload["report_type"] = report.report_type
        return payload

    if resource_type == "DocType":
        reference = row.reference_doctype
        if not reference or not frappe.db.exists("DocType", reference):
            return None
        meta = frappe.get_meta(reference)
        if meta.istable or not frappe.has_permission(reference, "read"):
            return None
        label = row.display_label or frappe._(reference)
        payload = _open_item_payload(row, reference, label, "doctype", "list")
        payload["is_single"] = bool(meta.issingle)
        return payload

    return None


def _open_item_payload(row, reference, label, resource_type, default_icon):
    return {
        "resource_type": resource_type,
        "reference": reference,
        "label": label,
        "group": row.menu_group or "Open",
        "description": row.description or "",
        "icon": row.icon or default_icon,
        "favorite": bool(row.is_favorite),
        "sequence": int(row.sequence or 10),
    }
