from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.utils import add_to_date, now_datetime, today

from qorg.qorg.people_and_opportunities.portal import is_opportunity_open


@frappe.whitelist()
def start_participation_application(
    opportunity: str | None = None,
    external_opportunity: str | None = None,
    qorg_external_opportunity: str | None = None,
    route: str | None = None,
):
    if frappe.session.user == "Guest":
        frappe.throw(_("Please sign in before applying."), frappe.PermissionError)
    opportunity_value = (
        opportunity or external_opportunity or qorg_external_opportunity or route
        or frappe.form_dict.get("opportunity")
        or frappe.form_dict.get("external_opportunity")
        or frappe.form_dict.get("qorg_external_opportunity")
        or frappe.form_dict.get("route") or ""
    )
    opportunity_value = str(opportunity_value).strip()
    if not opportunity_value or opportunity_value.lower() in {"none", "null", "undefined"}:
        frappe.throw(_("A valid external opportunity is required to start an application."))
    opportunity_name = opportunity_value
    if not frappe.db.exists("External Opportunity", opportunity_name):
        opportunity_name = frappe.db.get_value("External Opportunity", {"route": opportunity_value}, "name")
    if not opportunity_name:
        frappe.throw(_("The selected external opportunity does not exist."))
    opportunity_doc = frappe.get_doc("External Opportunity", opportunity_name)
    if not is_opportunity_open(opportunity_doc):
        frappe.throw(_("Applications are closed for this opportunity."))
    person = _owned_external_profile(frappe.session.user)
    if not person:
        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = "/external-profile-form"
        return
    existing = frappe.db.get_value(
        "Participation Application",
        {"opportunity": opportunity_doc.name, "external_person": ["in", person_names], "status": ["!=", "Cancelled"]},
        "name",
    )
    if existing:
        request = _create_web_form_request(values={}, reference_doctype="Participation Application", reference_docname=existing)
        _redirect_to_participation_form(request, existing)
        return
    participation_type = opportunity_doc.get("qorg_participation_type") or opportunity_doc.get("participation_type") or "Volunteer"
    values = {"opportunity": opportunity_doc.name, "external_person": person.name, "participation_type": participation_type, "application_date": today(), "status": "Draft"}
    request = _create_web_form_request(values=values)
    _redirect_to_participation_form(request)


def _create_web_form_request(
    values: dict,
    reference_doctype: str | None = None,
    reference_docname: str | None = None,
):
    web_form = frappe.db.get_value(
        "Web Form", {"route": "participation-application"}, "name"
    )
    if not web_form:
        frappe.throw(_("Participation Application Web Form is not configured."))

    request = frappe.new_doc("Web Form Request")
    request.web_form = web_form
    request.web_form_values = json.dumps(values or {})
    request.doc_values = json.dumps(values or {})

    if reference_doctype and reference_docname:
        request.append(
            "references",
            {
                "link_doctype": reference_doctype,
                "link_name": reference_docname,
            },
        )

    if request.meta.has_field("expires_on"):
        request.expires_on = add_to_date(now_datetime(), hours=2)

    request.insert(ignore_permissions=True)

    # This whitelisted workflow is opened through a portal link (HTTP GET).
    # Persist the request before redirecting to the Web Form.
    frappe.db.commit()
    return request


def _redirect_to_participation_form(request, docname: str | None = None):
    key = request.get("key") or request.name
    path = "/participation-application"
    path += f"/{docname}" if docname else "/new"

    frappe.local.response["type"] = "redirect"
    frappe.local.response["location"] = f"{path}?web_form_request_key={key}"


def _owned_external_profile(user: str):
    active = {"person_status": ["!=", "Merged"]}
    name = frappe.db.get_value("External Person", {**active, "owner": user}, "name", order_by="creation desc")
    if not name and frappe.get_meta("External Person").has_field("user"):
        name = frappe.db.get_value("External Person", {**active, "user": user}, "name", order_by="creation desc")
    return frappe.get_doc("External Person", name) if name else None

