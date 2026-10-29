from __future__ import annotations

import frappe
from frappe import _

from qorg.qorg.people_and_opportunities.portal import (
    get_my_applications,
    get_public_opportunities,
    get_public_opportunity,
)
from qorg.qorg.people_and_opportunities.portal_settings import (
    get_opportunity_portal_settings,
)


def get_opportunities_context(context):
    settings = get_opportunity_portal_settings()
    if not settings.enabled:
        raise frappe.PageDoesNotExistError
    context.no_cache = 1
    context.title = _("Opportunities")
    context.opportunities = get_public_opportunities(
        filters=frappe.form_dict,
        limit_start=frappe.form_dict.get("start") or 0,
        limit_page_length=settings.page_size,
    )
    context.applications_enabled = settings.applications_enabled
    context.filters = frappe.form_dict
    context.is_guest = frappe.session.user == "Guest"
    context.is_rtl = frappe.local.lang in ("ar", "he", "fa", "ur")
    return context


def get_opportunity_context(context):
    context.no_cache = 1
    route = frappe.form_dict.get("route")
    try:
        opportunity = get_public_opportunity(route)
    except frappe.PermissionError:
        frappe.local.flags.redirect_location = "/login?redirect-to=/opportunities/{}".format(route)
        raise frappe.Redirect
    except frappe.DoesNotExistError:
        raise frappe.PageDoesNotExistError
    context.opportunity = opportunity
    context.portal_settings = get_opportunity_portal_settings()
    context.title = opportunity.get("opportunity_title") or _("Opportunity")
    context.is_guest = frappe.session.user == "Guest"
    context.user_email = None if context.is_guest else frappe.session.user
    context.is_rtl = frappe.local.lang in ("ar", "he", "fa", "ur")
    return context


def get_my_applications_context(context):
    if not get_opportunity_portal_settings().enabled:
        raise frappe.PageDoesNotExistError
    context.no_cache = 1
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=/my-applications"
        raise frappe.Redirect
    context.title = _("My Applications")
    context.applications = get_my_applications()
    context.is_rtl = frappe.local.lang in ("ar", "he", "fa", "ur")
    return context
