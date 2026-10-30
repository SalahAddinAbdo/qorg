from __future__ import annotations

from urllib.parse import quote, urlencode

import frappe
from frappe import _

from qorg.qorg.people_and_opportunities.portal import (
    _get_external_person_for_user,
    _get_external_person_names_for_user,
    get_public_opportunities,
    get_public_opportunity,
)


def _is_rtl_language() -> bool:
    return (frappe.local.lang or "").lower() in {"ar", "he", "fa", "ur"}


def get_opportunities_context(context):
    context.no_cache = 1
    context.title = _("Opportunities")
    context.opportunities = get_public_opportunities(
        filters=frappe.form_dict,
        limit_start=frappe.form_dict.get("start") or 0,
        limit_page_length=24,
    )
    context.filters = frappe.form_dict
    context.is_guest = frappe.session.user == "Guest"
    context.page_is_rtl = _is_rtl_language()
    return context


def get_opportunity_context(context):
    context.no_cache = 1
    route = (frappe.form_dict.get("route") or "").strip()
    try:
        opportunity = get_public_opportunity(route)
    except frappe.PermissionError:
        frappe.local.flags.redirect_location = f"/login?redirect-to={quote(f'/opportunities/{route}', safe='')}"
        raise frappe.Redirect
    except frappe.DoesNotExistError:
        raise frappe.PageDoesNotExistError

    context.opportunity = opportunity
    context.title = opportunity.get("opportunity_title") or _("Opportunity")
    context.is_guest = frappe.session.user == "Guest"
    context.page_is_rtl = _is_rtl_language()
    context.apply_action = "closed"
    context.application_action_url = None

    if not opportunity.get("is_open"):
        return context
    if context.is_guest:
        context.apply_action = "login"
        context.application_action_url = f"/login?redirect-to={quote(f'/opportunities/{route}', safe='')}"
        return context

    profile_names = _get_external_person_names_for_user(frappe.session.user)

    if not profile_names:
        context.apply_action = "profile"
        context.application_action_url = "/external-profile-form"
        return context

    existing = frappe.db.get_value(
        "Participation Application",
        {
            "opportunity": opportunity.name,
            "external_person": ["in", profile_names],
            "status": ["!=", "Cancelled"],
        },
        "name",
    ) or frappe.db.get_value(
        "Participation Application",
        {
            "opportunity": opportunity.name,
            "owner": frappe.session.user,
            "status": ["!=", "Cancelled"],
        },
        "name",
    )
    if existing:
        context.apply_action = "existing"
        context.application_action_url = opportunity.get("apply_url")
    else:
        context.apply_action = "apply"
        context.application_action_url = opportunity.get("apply_url")
    return context
