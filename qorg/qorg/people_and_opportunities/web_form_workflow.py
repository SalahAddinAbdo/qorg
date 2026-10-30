from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.utils import add_to_date, now_datetime, today

from qorg.qorg.people_and_opportunities.portal import is_opportunity_open


@frappe.whitelist()
def start_participation_application(opportunity: str | None = None):
    if frappe.session.user == "Guest":
        frappe.throw(_("Please sign in before applying."), frappe.PermissionError)

    opportunity = (opportunity or "").strip()
    if not opportunity or opportunity.lower() in {"none", "null", "undefined"}:
        frappe.throw(_("A valid external opportunity is required to start an application."))

    opportunity_doc = frappe.get_doc("External Opportunity", opportunity)
    if not is_opportunity_open(opportunity_doc):
        frappe.throw(_("Applications are closed for this opportunity."))

    person = _owned_external_profile(frappe.session.user)
    if not person:
        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = "/external-profile-form"
        return

    existing = frappe.db.get_value(
        "Participation Application",
        {
            "opportunity": opportunity_doc.name,
            "external_person": person.name,
            "status": ["!=", "Cancelled"],
        },
        "name",
    )
    if existing:
        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = f"/participation-application/{existing}"
        return

    participation_type = (
        opportunity_doc.get("qorg_participation_type")
        or opportunity_doc.get("participation_type")
        or "Volunteer"
    )
    values = {
        "opportunity": opportunity_doc.name,
        "external_person": person.name,
        "participation_type": participation_type,
        "application_date": today(),
        "status": "Draft",
    }

    request = frappe.new_doc("Web Form Request")
    request.web_form = frappe.db.get_value(
        "Web Form", {"route": "participation-application"}, "name"
    )
    request.web_form_values = json.dumps(values)
    request.doc_values = json.dumps(values)
    if request.meta.has_field("expires_on"):
        request.expires_on = add_to_date(now_datetime(), hours=2)
    request.insert(ignore_permissions=True)

    # This whitelisted workflow is opened through a portal link (HTTP GET).
    # Frappe does not commit database writes made by successful GET requests,
    # so persist the short-lived request before redirecting to the Web Form.
    frappe.db.commit()

    key = request.get("key") or request.name
    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = (
        f"/participation-application/new?web_form_request_key={key}"
    )


def _owned_external_profile(user: str):
    name = frappe.db.get_value(
        "External Person",
        {"owner": user, "person_status": ["!=", "Merged"]},
        "name",
        order_by="creation desc",
    )
    if not name:
        name = frappe.db.get_value("External Person", {"user": user}, "name")
    return frappe.get_doc("External Person", name) if name else None
