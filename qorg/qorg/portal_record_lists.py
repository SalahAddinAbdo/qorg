from __future__ import annotations

from urllib.parse import quote

import frappe
from frappe import _

PAGE_LENGTH = 24

LIST_DEFINITIONS = {
    "applications": {
        "doctype": "Participation Application",
        "eyebrow": "People and Opportunities Portal",
        "title": "My Applications",
        "description": "Review draft, submitted and evaluated applications linked to your professional profile.",
        "history_title": "Application History",
        "browse_label": "Browse Opportunities",
        "browse_url": "/opportunities",
        "profile_label": "My Profile",
        "profile_url": "/external-profile-form",
        "empty_title": "No applications yet",
        "empty_description": "Open a published opportunity to start an application with your professional profile.",
    },
    "bids": {
        "doctype": "Procurement Submission",
        "eyebrow": "Supplier Portal",
        "title": "My Bids",
        "description": "Review draft, submitted, withdrawn and evaluated bids linked to your supplier profile.",
        "history_title": "Bid History",
        "browse_label": "Browse Opportunities",
        "browse_url": "/procurement",
        "profile_label": "Supplier Profile",
        "profile_url": "/supplier-profile",
        "empty_title": "No bids yet",
        "empty_description": "Open a published procurement opportunity to start the tender form directly.",
    },
}


def _page_start():
    try:
        return max(0, int(frappe.form_dict.get("start") or 0))
    except (TypeError, ValueError):
        return 0


def _application_rows(start, page_length):
    person_names = frappe.get_all(
        "External Person",
        filters={"user": frappe.session.user},
        pluck="name",
    ) if frappe.get_meta("External Person").has_field("user") else []
    or_filters = [["Participation Application", "owner", "=", frappe.session.user]]
    if person_names:
        or_filters.append(["Participation Application", "external_person", "in", person_names])

    rows = frappe.get_all(
        "Participation Application",
        or_filters=or_filters,
        fields=["name", "opportunity", "participation_type", "application_date", "status", "modified"],
        order_by="modified desc",
        limit_start=start,
        limit_page_length=page_length + 1,
    )
    opportunity_names = [row.opportunity for row in rows if row.opportunity]
    opportunity_map = {
        row.name: row
        for row in frappe.get_all(
            "External Opportunity",
            filters={"name": ["in", opportunity_names]},
            fields=["name", "opportunity_title", "route"],
        )
    } if opportunity_names else {}

    result = []
    for row in rows[:page_length]:
        opportunity = opportunity_map.get(row.opportunity)
        result.append({
            "name": row.name,
            "title": opportunity.opportunity_title if opportunity else (row.opportunity or row.name),
            "status": row.status or "Draft",
            "type": row.participation_type or _("Application"),
            "date_label": _("Application Date"),
            "date": row.application_date,
            "reference": row.name,
            "open_label": _("Open Application"),
            "open_url": (
                "/api/method/qorg.qorg.people_and_opportunities.web_form_workflow."
                f"open_participation_application?application={quote(row.name, safe='')}"
            ),
            "source_label": _("View Opportunity"),
            "source_url": f"/opportunities/{quote(opportunity.route, safe='')}" if opportunity and opportunity.route else None,
        })
    return result, len(rows) > page_length


def _bid_rows(start, page_length):
    rows = frappe.get_all(
        "Procurement Submission",
        filters={"owner": frappe.session.user},
        fields=["name", "procurement_process", "procurement_notice", "submission_status", "submitted_at", "submission_version", "modified"],
        order_by="modified desc",
        limit_start=start,
        limit_page_length=page_length + 1,
    )
    notice_names = [row.procurement_notice for row in rows if row.procurement_notice]
    notice_map = {
        row.name: row
        for row in frappe.get_all(
            "Procurement Notice",
            filters={"name": ["in", notice_names]},
            fields=["name", "title", "route"],
        )
    } if notice_names else {}

    result = []
    for row in rows[:page_length]:
        notice = notice_map.get(row.procurement_notice)
        type_label = _("Bid")
        if row.submission_version:
            type_label = _("Bid Version {0}").format(row.submission_version)
        result.append({
            "name": row.name,
            "title": notice.title if notice else (row.procurement_process or row.name),
            "status": row.submission_status or "Draft",
            "type": type_label,
            "date_label": _("Submitted"),
            "date": row.submitted_at,
            "reference": row.name,
            "open_label": _("Open Bid"),
            "open_url": (
                "/api/method/qorg.qorg.procurement_contracting.portal_workflow."
                f"open_tender_submission?submission={quote(row.name, safe='')}"
            ),
            "source_label": _("View Opportunity"),
            "source_url": f"/procurement-opportunity?route={quote(notice.route, safe='')}" if notice and notice.route else None,
        })
    return result, len(rows) > page_length


def get_portal_record_list_context(context, list_key):
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = f"/login?redirect-to=/{'my-applications' if list_key == 'applications' else 'my-bids'}"
        raise frappe.Redirect

    definition = LIST_DEFINITIONS[list_key]
    start = _page_start()
    if list_key == "applications":
        records, has_more = _application_rows(start, PAGE_LENGTH)
    else:
        records, has_more = _bid_rows(start, PAGE_LENGTH)

    context.no_cache = 1
    context.title = _(definition["title"])
    context.portal_list = {
        **{key: _(value) if key not in {"browse_url", "profile_url"} else value for key, value in definition.items()},
        "records": records,
        "count": len(records),
        "start": start,
        "page_length": PAGE_LENGTH,
        "previous_start": max(0, start - PAGE_LENGTH) if start else None,
        "next_start": start + PAGE_LENGTH if has_more else None,
    }
    return context
