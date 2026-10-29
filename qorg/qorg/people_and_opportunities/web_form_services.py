from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint, getdate, now_datetime, today
from frappe.website.utils import delete_page_cache

LOCKED_APPLICATION_STATUSES = {
    "Under Screening", "Screening Completed", "Under Assessment", "Selected",
    "Reserve / Waitlisted", "Rejected", "Disqualified", "Cancelled", "Closed",
}
EXCLUDED_CAPACITY_STATUSES = {"Withdrawn", "Cancelled"}


def validate_external_person_portal_access(doc, method=None):
    if not _is_website_user():
        _maintain_lock_audit(doc)
        return

    if doc.is_new():
        existing = frappe.db.get_value("External Person", {"user": frappe.session.user}, "name")
        if existing:
            frappe.throw(_("This account already has an external profile: {0}").format(existing))
        _set(doc, "user", frappe.session.user)
        _set(doc, "primary_email", frappe.session.user)
        _set(doc, "allow_portal_editing", 1)
        return

    if doc.get("user") != frappe.session.user:
        frappe.throw(_("You can update only your own external profile."), frappe.PermissionError)

    old = doc.get_doc_before_save()
    if old and not cint(old.get("allow_portal_editing")):
        frappe.throw(old.get("portal_edit_lock_reason") or _("Profile editing is locked by the organization."))

    protected = (
        "user", "allow_portal_editing", "portal_edit_lock_reason",
        "portal_edit_locked_by", "portal_edit_locked_on",
    )
    for fieldname in protected:
        if old and doc.get(fieldname) != old.get(fieldname):
            doc.set(fieldname, old.get(fieldname))


def validate_participation_application_portal(doc, method=None):
    if not _is_website_user():
        return
    _validate_application(doc, "opportunity", "external_person")
    _set(doc, "application_source", "Portal")
    _set(doc, "portal_owner", frappe.session.user)


def validate_job_applicant_portal(doc, method=None):
    if not _is_website_user():
        return
    _validate_application(doc, "qorg_external_opportunity", "qorg_external_person")
    _set(doc, "source", "Portal")


def reconcile_participation_application_capacity(doc, method=None):
    _reconcile(doc.get("opportunity"))


def reconcile_job_applicant_capacity(doc, method=None):
    fieldname = "qorg_external_opportunity"
    _reconcile(doc.get(fieldname) if doc.meta.has_field(fieldname) else None)


def count_opportunity_applications(opportunity_name):
    total = 0
    if frappe.db.exists("DocType", "Participation Application"):
        filters = {"opportunity": opportunity_name}
        if frappe.get_meta("Participation Application").has_field("status"):
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


def is_application_capacity_available(opportunity_name):
    doc = frappe.get_doc("External Opportunity", opportunity_name)
    limit_value = cint(doc.get("application_limit"))
    return limit_value <= 0 or count_opportunity_applications(opportunity_name) < limit_value


def _validate_application(doc, opportunity_field, person_field):
    opportunity_name = doc.get(opportunity_field)
    if not opportunity_name:
        frappe.throw(_("Open this form from a published opportunity."))

    frappe.db.sql(
        "select name from `tabExternal Opportunity` where name=%s for update",
        opportunity_name,
    )
    opportunity = frappe.get_doc("External Opportunity", opportunity_name)
    from qorg.qorg.people_and_opportunities.portal import is_opportunity_open

    if not is_opportunity_open(opportunity):
        frappe.throw(_("Applications are closed for this opportunity."))

    person = _person_for_user(frappe.session.user)
    if not person:
        frappe.throw(_("Create your external profile before applying."))

    _set(doc, person_field, person.name)
    _set(doc, "applicant_name", person.get("full_name"))
    _set(doc, "email", person.get("primary_email"))
    _set(doc, "email_id", person.get("primary_email"))
    _set(doc, "mobile_no", person.get("mobile_no"))
    _set(doc, "phone_number", person.get("mobile_no"))
    _set(doc, "company", opportunity.get("company"))
    _set(doc, "project", opportunity.get("project"))
    _set(doc, "branch", opportunity.get("branch"))
    _set(doc, "participation_type", opportunity.get("participation_type"))
    _set(doc, "job_title", opportunity.get("job_opening"))

    if doc.is_new():
        existing = frappe.db.get_value(
            doc.doctype,
            {opportunity_field: opportunity_name, person_field: person.name},
            "name",
        )
        if existing:
            frappe.throw(_("You already submitted an application for this opportunity: {0}").format(existing))
    else:
        old = doc.get_doc_before_save()
        if old:
            doc.set(opportunity_field, old.get(opportunity_field))
            doc.set(person_field, old.get(person_field))
        _assert_application_editable(doc, opportunity)


def _assert_application_editable(doc, opportunity):
    settings = frappe.get_single("HR Settings")
    if cint(settings.get("qorg_allow_application_edit_until_closing") or 1):
        if opportunity.get("closing_date") and getdate(opportunity.closing_date) < getdate(today()):
            frappe.throw(_("This application cannot be edited because the opportunity is closed."))
    if cint(settings.get("qorg_lock_application_when_screening_starts") or 1):
        if doc.get("status") in LOCKED_APPLICATION_STATUSES:
            frappe.throw(_("This application is locked because screening or assessment has started."))


def _reconcile(opportunity_name):
    if not opportunity_name or not frappe.db.exists("External Opportunity", opportunity_name):
        return
    doc = frappe.get_doc("External Opportunity", opportunity_name)
    count = count_opportunity_applications(opportunity_name)
    limit_value = cint(doc.get("application_limit"))
    remaining = max(limit_value - count, 0) if limit_value > 0 else 0
    updates = {}
    for fieldname, value in (
        ("applications_received", count),
        ("remaining_application_capacity", remaining),
    ):
        if doc.meta.has_field(fieldname) and doc.get(fieldname) != value:
            updates[fieldname] = value

    if limit_value > 0 and count >= limit_value:
        if doc.meta.has_field("application_limit_reached_on") and not doc.get("application_limit_reached_on"):
            updates["application_limit_reached_on"] = now_datetime()
        if doc.meta.has_field("applications_closed_reason"):
            updates["applications_closed_reason"] = _("Maximum application limit reached")
        if cint(doc.get("close_automatically_at_application_limit")) and doc.get("status") == "Published":
            updates["status"] = "Closed"

    if updates:
        frappe.db.set_value("External Opportunity", opportunity_name, updates, update_modified=True)
        delete_page_cache()


def _person_for_user(user):
    name = frappe.db.get_value("External Person", {"user": user}, "name")
    return frappe.get_doc("External Person", name) if name else None


def _maintain_lock_audit(doc):
    old = doc.get_doc_before_save()
    if not old or not doc.meta.has_field("allow_portal_editing"):
        return
    if cint(old.get("allow_portal_editing")) and not cint(doc.get("allow_portal_editing")):
        _set(doc, "portal_edit_locked_by", frappe.session.user)
        _set(doc, "portal_edit_locked_on", now_datetime())
    elif not cint(old.get("allow_portal_editing")) and cint(doc.get("allow_portal_editing")):
        _set(doc, "portal_edit_locked_by", None)
        _set(doc, "portal_edit_locked_on", None)
        _set(doc, "portal_edit_lock_reason", None)


def _is_website_user():
    if frappe.session.user in ("Guest", "Administrator"):
        return False
    return frappe.db.get_value("User", frappe.session.user, "user_type") == "Website User"


def _set(doc, fieldname, value):
    if doc.meta.has_field(fieldname) and value is not None:
        doc.set(fieldname, value)
