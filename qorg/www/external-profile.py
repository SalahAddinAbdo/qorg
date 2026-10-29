from __future__ import annotations

import frappe
from frappe import _

from qorg.qorg.people_and_opportunities.web_form_services import (
    get_external_person_for_user,
)


def get_context(context):
    context.no_cache = 1
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=/external-profile"
        raise frappe.Redirect

    person = get_external_person_for_user(frappe.session.user)
    context.title = _("External Profile")
    context.person = person
    context.profile_exists = bool(person)
    context.profile_locked = bool(person and not int(person.get("allow_portal_editing") or 0))
    context.lock_reason = person.get("portal_edit_lock_reason") if person else None
    context.profile_form_url = (
        f"/external-profile-form/{person.name}/edit"
        if person and not context.profile_locked
        else "/external-profile-form/new"
    )
    context.page_is_rtl = (frappe.local.lang or "").lower() in {"ar", "he", "fa", "ur"}
    context.cv_html = ""
    if person:
        try:
            context.cv_html = frappe.render_template(
                "qorg/qorg/people_and_opportunities/templates/external_person_cv.html",
                {"doc": person, "person": person},
            )
        except Exception:
            context.cv_html = ""
    return context
