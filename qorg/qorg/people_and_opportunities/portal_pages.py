from __future__ import annotations

from urllib.parse import quote, urlencode

import frappe
from frappe import _

from qorg.qorg.doctype.participation_application.participation_application import (
    get_external_person_for_user,
    get_participation_type,
)
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
    try:
        opportunity = get_public_opportunity(route)
    except frappe.PermissionError:
        frappe.local.flags.redirect_location = (
            f"/login?redirect-to={quote(f'/opportunities/{route}', safe='')}"
        )
        raise frappe.Redirect
    except frappe.DoesNotExistError:
        raise frappe.PageDoesNotExistError

    context.opportunity = opportunity
    context.title = opportunity.get("opportunity_title") or _("Opportunity")
    context.is_guest = frappe.session.user == "Guest"
    context.user_email = None if context.is_guest else frappe.session.user
    context.page_is_rtl = _is_rtl_language()
    context.apply_action = "closed"
    context.application_action_url = None
    context.profile_creation_url = None
    context.existing_application = None

    if not opportunity.is_open:
        return context

    return_path = f"/opportunities/{route}"
    if context.is_guest:
        context.apply_action = "login"
        context.application_action_url = (
            f"/login?redirect-to={quote(return_path, safe='')}"
        )
        return context

    person = get_external_person_for_user(frappe.session.user)
    if not person:
        context.apply_action = "profile"
        context.profile_creation_url = "/external-profile?" + urlencode(
            {"return_to": return_path}
        )
        context.application_action_url = context.profile_creation_url
        return context

    if opportunity.get("application_doctype") == "Job Applicant":
        existing = _find_existing_job_application(opportunity, person)
        if existing:
            context.apply_action = "existing"
            context.existing_application = existing
            context.application_action_url = f"/employment-application/{quote(existing)}"
        else:
            context.apply_action = "apply"
            context.application_action_url = "/employment-application/new?" + urlencode(
                {
                    "qorg_external_opportunity": opportunity.name,
                    "qorg_external_person": person.name,
                }
            )
        return context

    existing = _find_existing_participation_application(opportunity.name, person.name)
    if existing:
        context.apply_action = "existing"
        context.existing_application = existing
        context.application_action_url = f"/participation-application/{quote(existing)}"
    else:
        source = frappe.get_doc("External Opportunity", opportunity.name)
        context.apply_action = "apply"
        context.application_action_url = "/participation-application/new?" + urlencode(
            {
                "opportunity": opportunity.name,
                "external_person": person.name,
                "participation_type": get_participation_type(source),
            }
        )
    return context


def _find_existing_participation_application(opportunity: str, person: str):
    rows = frappe.db.sql(
        """
        select name
          from `tabParticipation Application`
         where opportunity = %s
           and external_person = %s
           and coalesce(status, '') != 'Cancelled'
           and coalesce(final_decision, '') not in ('Withdrawn', 'Cancelled')
         order by creation desc
         limit 1
        """,
        (opportunity, person),
        as_dict=True,
    )
    return rows[0].name if rows else None


def _find_existing_job_application(opportunity, person):
    meta = frappe.get_meta("Job Applicant")
    if meta.has_field("qorg_external_opportunity") and meta.has_field("qorg_external_person"):
        return frappe.db.get_value(
            "Job Applicant",
            {
                "qorg_external_opportunity": opportunity.name,
                "qorg_external_person": person.name,
            },
            "name",
        )
    if opportunity.get("job_opening") and person.get("primary_email"):
        return frappe.db.get_value(
            "Job Applicant",
            {
                "job_title": opportunity.job_opening,
                "email_id": person.primary_email,
            },
            "name",
        )
    return None


def get_my_applications_context(context):
    context.no_cache = 1
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=/my-applications"
        raise frappe.Redirect
    context.title = _("My Applications")
    context.applications = get_my_applications()
    context.page_is_rtl = _is_rtl_language()
    return context
