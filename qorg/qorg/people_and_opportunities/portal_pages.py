from __future__ import annotations

import frappe
from frappe import _

from qorg.qorg.doctype.external_person.external_person import resolve_external_person_for_user

from qorg.qorg.people_and_opportunities.portal import (
    get_my_applications,
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
    route = frappe.form_dict.get("route")

    try:
        opportunity = get_public_opportunity(route)
    except frappe.PermissionError:
        frappe.local.flags.redirect_location = (
            f"/login?redirect-to=/opportunities/{route}"
        )
        raise frappe.Redirect
    except frappe.DoesNotExistError:
        raise frappe.PageDoesNotExistError

    context.opportunity = opportunity
    context.title = opportunity.get("opportunity_title") or _("Opportunity")
    context.is_guest = frappe.session.user == "Guest"
    context.user_email = None if context.is_guest else frappe.session.user
    context.page_is_rtl = _is_rtl_language()
    return context


def get_my_applications_context(context):
    context.no_cache = 1

    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=/my-applications"
        raise frappe.Redirect

    context.title = _("My Applications")
    context.applications = get_my_applications()
    context.page_is_rtl = _is_rtl_language()
    return context
