from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint

from qorg.qorg.design_system.service import SETTINGS, baseline_status


@frappe.whitelist()
def get_baseline_status():
    return baseline_status()


@frappe.whitelist()
def get_quick_create_menu():
    if frappe.session.user == "Guest":
        return {"items": [], "grouped": {}}
    settings = frappe.get_single(SETTINGS)
    items = []
    seen = set()
    for row in settings.get("quick_create_items") or []:
        doctype = row.reference_doctype
        if not row.enabled or not doctype or doctype in seen or not frappe.db.exists("DocType", doctype):
            continue
        meta = frappe.get_meta(doctype)
        if meta.istable or meta.issingle or not frappe.has_permission(doctype, "create"):
            continue
        seen.add(doctype)
        items.append({
            "doctype": doctype,
            "label": row.display_label or _(doctype),
            "group": row.menu_group or _("Other"),
            "description": row.description or "",
            "icon": row.icon or "add",
            "favorite": cint(row.is_favorite),
            "sequence": row.sequence or 0,
        })
    items.sort(key=lambda item: (not item["favorite"], item["group"], item["sequence"], item["label"]))
    grouped = {}
    for item in items:
        grouped.setdefault(item["group"], []).append(item)
    return {"items": items, "grouped": grouped}


@frappe.whitelist()
def get_available_languages():
    if frappe.session.user == "Guest":
        frappe.throw(_("Please sign in first."), frappe.PermissionError)
    languages = frappe.get_all(
        "Language",
        filters={"enabled": 1},
        fields=["language_code", "language_name"],
        order_by="language_name",
    )
    return {"current": frappe.local.lang, "languages": languages}


@frappe.whitelist(methods=["POST"])
def set_current_user_language(language):
    if frappe.session.user == "Guest":
        frappe.throw(_("Please sign in first."), frappe.PermissionError)
    if not frappe.db.exists("Language", {"language_code": language, "enabled": 1}):
        frappe.throw(_("Language is not enabled."))
    frappe.db.set_value("User", frappe.session.user, "language", language)
    frappe.clear_cache(user=frappe.session.user)
    return {"language": language}
