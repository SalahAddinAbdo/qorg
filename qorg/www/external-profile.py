from __future__ import annotations

import frappe
from frappe import _


def get_context(context):
    context.no_cache = 1
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=/external-profile"
        raise frappe.Redirect

    name = frappe.db.get_value(
        "External Person",
        {"user": frappe.session.user},
        "name",
    )
    person = frappe.get_doc("External Person", name) if name else None

    context.title = _("External Profile")
    context.person = person
    context.profile_exists = bool(person)
    context.profile_locked = bool(
        person and not int(person.get("allow_portal_editing") or 0)
    )
    context.lock_reason = (
        person.get("portal_edit_lock_reason") if person else None
    )
    context.edit_url = (
        f"/external-profile-form/{person.name}/edit" if person else None
    )
    context.page_is_rtl = (frappe.local.lang or "").lower() in {
        "ar",
        "he",
        "fa",
        "ur",
    }
    return context
