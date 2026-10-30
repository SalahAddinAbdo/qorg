from __future__ import annotations

from urllib.parse import quote, urlencode

import frappe
from frappe import _

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
    route = (frappe.form_dict.get("route") or "").strip()
    if not route:
        raise frappe.PageDoesNotExistError

    try:
        opportunity = get_public_opportunity(route)
    except frappe.PermissionError:
        frappe.local.flags.redirect_location = (
            f"/login?redirect-to={quote(f'/opportunities/{route}', safe='')}"
        )
        raise frappe.Redirect
    except frappe.DoesNotExistError:
        raise frappe.PageDoesNotExistError

    # The public serializer returns presentation data and does not expose the
    # internal document name. Resolve the canonical name from the route.
    opportunity_name = frappe.db.get_value(
        "External Opportunity",
        {"route": route},
        "name",
    )
    if not opportunity_name:
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
        context.application_action_url = (
            f"/login?redirect-to={quote(f'/opportunities/{route}', safe='')}"
        )
        return context

    profile = frappe.db.get_value(
        "External Person",
        {
            "owner": frappe.session.user,
            "person_status": ["!=", "Merged"],
        },
        "name",
        order_by="creation desc",
    ) or frappe.db.get_value(
        "External Person",
        {"user": frappe.session.user},
        "name",
    )

    if not profile:
        context.apply_action = "profile"
        context.application_action_url = "/external-profile-form"
        return context

    existing = frappe.db.get_value(
        "Participation Application",
        {
            "opportunity": opportunity_name,
            "external_person": profile,
            "status": ["!=", "Cancelled"],
        },
        "name",
    )
    if existing:
        context.apply_action = "existing"
        context.application_action_url = f"/participation-application/{quote(existing)}"
    else:
        context.apply_action = "apply"
        context.application_action_url = (
            "/api/method/qorg.qorg.people_and_opportunities.web_form_workflow."
            "start_participation_application?"
            + urlencode({"opportunity": opportunity_name})
        )

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
