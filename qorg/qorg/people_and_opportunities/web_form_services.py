from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint, getdate, now_datetime, today

LOCKED_APPLICATION_STATUSES = {
    "Under Screening", "Screening Completed", "Under Assessment", "Selected",
    "Reserve / Waitlisted", "Rejected", "Disqualified", "Cancelled", "Closed",
}
EXCLUDED_CAPACITY_STATUSES = {"Withdrawn", "Cancelled"}


@frappe.whitelist()
def get_profile_web_form_state():
    _require_login()
    person = get_external_person_for_user(frappe.session.user)
    return {
        "name": person.name if person else None,
        "locked": bool(person and not cint(person.get("allow_portal_editing"))),
        "lock_reason": person.get("portal_edit_lock_reason") if person else None,
        "view_url": "/external-profile",
        "edit_url": f"/external-profile-form/{person.name}/edit" if person else "/external-profile-form/new",
    }


@frappe.whitelist()
def get_application_web_form_context(opportunity_route, target_doctype):
    _require_login()
    from qorg.qorg.people_and_opportunities.portal import (
        get_public_opportunity,
        is_opportunity_open,
    )
    public = get_public_opportunity(opportunity_route)
    opportunity = frappe.get_doc("External Opportunity", public.name)
    person = get_external_person_for_user(frappe.session.user)
    if not person:
        frappe.throw(_("Create your external profile before applying."))
    expected = _target_application_doctype(opportunity)
    if target_doctype != expected:
        frappe.throw(_("This application form does not match the opportunity type."))
    open_for_applications = is_opportunity_open(opportunity) and is_application_capacity_available(opportunity.name)
    values = _application_values(opportunity, person, target_doctype)
    return {
        "open": open_for_applications,
        "message": None if open_for_applications else _("Applications are closed for this opportunity."),
        "values": values,
        "profile_url": "/external-profile",
    }


def validate_external_person_portal_access(doc, method=None):
    if doc.is_new() and _is_website_user():
        existing = frappe.db.get_value("External Person", {"user": frappe.session.user}, "name")
        if existing:
            frappe.throw(_("This account already has an external profile: {0}").format(existing))
        _set_if_field(doc, "user", frappe.session.user)
        _set_if_field(doc, "primary_email", frappe.session.user)
        _set_if_field(doc, "allow_portal_editing", 1)
        return

    if not _is_website_user():
        maintain_profile_lock_audit(doc)
        return

    _assert_owned_external_person(doc)
    old = doc.get_doc_before_save()
    if old and not cint(old.get("allow_portal_editing")):
        frappe.throw(old.get("portal_edit_lock_reason") or _("Profile editing is locked by the organization."))
    for fieldname in ("user", "allow_portal_editing", "portal_edit_lock_reason", "portal_edit_locked_by", "portal_edit_locked_on"):
        if old and doc.get(fieldname) != old.get(fieldname):
            doc.set(fieldname, old.get(fieldname))


def validate_participation_application_portal(doc, method=None):
    if not _is_website_user():
        return
    _validate_application_doc(doc, "opportunity", "external_person")


def validate_job_applicant_portal(doc, method=None):
    if not _is_website_user():
        return
    _validate_application_doc(doc, "qorg_external_opportunity", "qorg_external_person")


def reconcile_participation_application_capacity(doc, method=None):
    opportunity = doc.get("opportunity")
    if opportunity:
        reconcile_opportunity_capacity(opportunity)


def reconcile_job_applicant_capacity(doc, method=None):
    opportunity = doc.get("qorg_external_opportunity") if doc.meta.has_field("qorg_external_opportunity") else None
    if opportunity:
        reconcile_opportunity_capacity(opportunity)


def is_application_capacity_available(opportunity_name):
    opportunity = frappe.get_doc("External Opportunity", opportunity_name)
    limit_value = cint(opportunity.get("application_limit"))
    if limit_value <= 0:
        return True
    return count_opportunity_applications(opportunity_name) < limit_value


def reconcile_opportunity_capacity(opportunity_name):
    if not opportunity_name or not frappe.db.exists("External Opportunity", opportunity_name):
        return
    opportunity = frappe.get_doc("External Opportunity", opportunity_name)
    count = count_opportunity_applications(opportunity_name)
    limit_value = cint(opportunity.get("application_limit"))
    remaining = max(limit_value - count, 0) if limit_value > 0 else 0
    updates = {}
    for fieldname, value in (
        ("applications_received", count),
        ("remaining_application_capacity", remaining),
    ):
        if opportunity.meta.has_field(fieldname) and opportunity.get(fieldname) != value:
            updates[fieldname] = value
    if limit_value > 0 and count >= limit_value:
        if opportunity.meta.has_field("application_limit_reached_on") and not opportunity.get("application_limit_reached_on"):
            updates["application_limit_reached_on"] = now_datetime()
        if opportunity.meta.has_field("applications_closed_reason"):
            updates["applications_closed_reason"] = _("Maximum application limit reached")
        if cint(opportunity.get("close_automatically_at_application_limit")) and opportunity.get("status") == "Published":
            updates["status"] = "Closed"
    if updates:
        frappe.db.set_value("External Opportunity", opportunity_name, updates, update_modified=True)
        from frappe.website.utils import delete_page_cache
        delete_page_cache()


def count_opportunity_applications(opportunity_name):
    total = 0
    if frappe.db.exists("DocType", "Participation Application"):
        filters = {"opportunity": opportunity_name}
        meta = frappe.get_meta("Participation Application")
        if meta.has_field("status"):
            filters["status"] = ["not in", list(EXCLUDED_CAPACITY_STATUSES)]
        total += frappe.db.count("Participation Application", filters)
    if frappe.db.exists("DocType", "Job Applicant"):
        meta = frappe.get_meta("Job Applicant")
        if meta.has_field("qorg_external_opportunity"):
            filters = {"qorg_external_opportunity": opportunity_name}
            if meta.has_field("status"):
                filters["status"] = ["not in", list(EXCLUDED_CAPACITY_STATUSES)]
            total += frappe.db.count("Job Applicant", filters)
    return total


def get_external_person_for_user(user):
    if not frappe.db.exists("DocType", "External Person"):
        return None
    meta = frappe.get_meta("External Person")
    if not meta.has_field("user"):
        return None
    name = frappe.db.get_value("External Person", {"user": user}, "name")
    return frappe.get_doc("External Person", name) if name else None


def _validate_application_doc(doc, opportunity_field, person_field):
    opportunity_name = doc.get(opportunity_field)
    if not opportunity_name:
        frappe.throw(_("Open the application form from a published opportunity."))
    frappe.db.sql("select name from `tabExternal Opportunity` where name=%s for update", opportunity_name)
    opportunity = frappe.get_doc("External Opportunity", opportunity_name)
    from qorg.qorg.people_and_opportunities.portal import is_opportunity_open
    if not is_opportunity_open(opportunity):
        frappe.throw(_("Applications are closed for this opportunity."))
    person = get_external_person_for_user(frappe.session.user)
    if not person:
        frappe.throw(_("Create your external profile before applying."))
    _set_if_field(doc, person_field, person.name)
    _set_if_field(doc, "applicant_name", person.get("full_name"))
    _set_if_field(doc, "email", person.get("primary_email"))
    _set_if_field(doc, "email_id", person.get("primary_email"))
    _set_if_field(doc, "mobile_no", person.get("mobile_no"))
    _set_if_field(doc, "phone_number", person.get("mobile_no"))
    _set_if_field(doc, "application_source", "Portal")
    _set_if_field(doc, "source", "Portal")
    _set_if_field(doc, "company", opportunity.get("company"))
    _set_if_field(doc, "project", opportunity.get("project"))
    _set_if_field(doc, "branch", opportunity.get("branch"))
    _set_if_field(doc, "participation_type", opportunity.get("participation_type"))
    _set_if_field(doc, "job_title", opportunity.get("job_opening"))
    if not doc.is_new():
        _assert_application_editable(doc, opportunity)
    else:
        _prevent_duplicate_application(doc, opportunity_field, person_field, person.name, opportunity_name)


def _assert_application_editable(doc, opportunity):
    allow_until_closing = cint(frappe.db.get_single_value("HR Settings", "qorg_allow_application_edit_until_closing") or 1)
    lock_on_screening = cint(frappe.db.get_single_value("HR Settings", "qorg_lock_application_when_screening_starts") or 1)
    if allow_until_closing and opportunity.get("closing_date") and getdate(opportunity.closing_date) < getdate(today()):
        frappe.throw(_("This application can no longer be edited because the opportunity is closed."))
    if lock_on_screening and doc.get("status") in LOCKED_APPLICATION_STATUSES:
        frappe.throw(_("This application is locked because screening or assessment has started."))


def _prevent_duplicate_application(doc, opportunity_field, person_field, person_name, opportunity_name):
    filters = {opportunity_field: opportunity_name, person_field: person_name}
    existing = frappe.db.get_value(doc.doctype, filters, "name")
    if existing:
        frappe.throw(_("You already submitted an application for this opportunity: {0}").format(existing))


def _target_application_doctype(opportunity):
    behavior = opportunity.get("opportunity_type")
    if frappe.db.exists("DocType", "External Opportunity Type") and behavior:
        behavior = frappe.db.get_value("External Opportunity Type", behavior, "behavior_code") or behavior
    return "Job Applicant" if behavior == "Employment" else "Participation Application"


def _application_values(opportunity, person, target_doctype):
    values = {}
    if target_doctype == "Participation Application":
        values.update({
            "opportunity": opportunity.name,
            "external_person": person.name,
            "participation_type": opportunity.get("participation_type") or "Volunteer",
            "application_date": today(),
            "applicant_name": person.get("full_name"),
            "email": person.get("primary_email"),
            "mobile_no": person.get("mobile_no"),
            "application_source": "Portal",
            "status": "Submitted",
        })
    else:
        values.update({
            "qorg_external_opportunity": opportunity.name,
            "qorg_external_person": person.name,
            "job_title": opportunity.get("job_opening"),
            "applicant_name": person.get("full_name"),
            "email_id": person.get("primary_email"),
            "phone_number": person.get("mobile_no"),
            "source": "Portal",
            "status": "Open",
        })
    return values


def _assert_owned_external_person(doc):
    if doc.get("user") != frappe.session.user:
        frappe.throw(_("You can update only your own external profile."), frappe.PermissionError)


def maintain_profile_lock_audit(doc, method=None):
    old = doc.get_doc_before_save()
    if not old or not doc.meta.has_field("allow_portal_editing"):
        return
    if cint(old.get("allow_portal_editing")) and not cint(doc.get("allow_portal_editing")):
        _set_if_field(doc, "portal_edit_locked_by", frappe.session.user)
        _set_if_field(doc, "portal_edit_locked_on", now_datetime())
    elif not cint(old.get("allow_portal_editing")) and cint(doc.get("allow_portal_editing")):
        _set_if_field(doc, "portal_edit_locked_by", None)
        _set_if_field(doc, "portal_edit_locked_on", None)
        _set_if_field(doc, "portal_edit_lock_reason", None)


def _is_website_user():
    if frappe.session.user in ("Guest", "Administrator"):
        return False
    return frappe.db.get_value("User", frappe.session.user, "user_type") == "Website User"


def _require_login():
    if frappe.session.user == "Guest":
        frappe.throw(_("Please sign in to continue."), frappe.PermissionError)


def _set_if_field(doc, fieldname, value):
    if doc.meta.has_field(fieldname) and value is not None:
        doc.set(fieldname, value)
