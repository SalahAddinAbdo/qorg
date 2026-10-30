from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, getdate, now_datetime, today
from frappe.website.utils import clear_cache as clear_website_cache

from qorg.qorg.volunteer_management import services

NON_CAPACITY_STATUSES = {"Cancelled"}
NON_CAPACITY_DECISIONS = {"Withdrawn", "Cancelled"}


class ParticipationApplication(Document):
    def before_validate(self):
        self._apply_portal_identity()

    def validate(self):
        self._validate_portal_application()
        services.validate_application(self)

    def after_insert(self):
        sync_opportunity_application_stats(self.opportunity)

    def on_update(self):
        previous = self.get_doc_before_save()
        sync_opportunity_application_stats(self.opportunity)
        if previous and previous.opportunity != self.opportunity:
            sync_opportunity_application_stats(previous.opportunity)

    def on_trash(self):
        self.flags.qorg_opportunity_to_sync = self.opportunity

    def after_delete(self):
        sync_opportunity_application_stats(
            getattr(self.flags, "qorg_opportunity_to_sync", None)
        )

    def _apply_portal_identity(self):
        if frappe.session.user == "Guest":
            frappe.throw(_("Please sign in before applying."), frappe.PermissionError)

        # Desk users may manage applications operationally. Website users can only
        # create and edit their own application/profile relationship.
        if frappe.db.get_value("User", frappe.session.user, "user_type") == "System User":
            return

        person = get_external_person_for_user(frappe.session.user)
        if not person:
            frappe.throw(
                _("Complete your external profile before applying."),
                frappe.ValidationError,
            )
        self.external_person = person.name
        self.profile_reviewed_by = frappe.session.user
        self.profile_reviewed_on = now_datetime()
        self.profile_modified_on_application = person.modified

    def _validate_portal_application(self):
        if not self.opportunity:
            frappe.throw(_("External Opportunity is required."))

        opportunity = lock_and_get_opportunity(self.opportunity)
        self.participation_type = get_participation_type(opportunity)
        self.application_date = self.application_date or today()
        self.status = self.status or "Draft"

        previous = self.get_doc_before_save()
        if self.is_new() or (previous and previous.opportunity != self.opportunity):
            _validate_opportunity_is_open(opportunity, self.name)
        _validate_duplicate_application(self)

        if frappe.db.get_value("User", frappe.session.user, "user_type") != "System User":
            person = get_external_person_for_user(frappe.session.user)
            if not person or person.name != self.external_person:
                frappe.throw(_("The application must use your own external profile."))
            if not cint(self.profile_review_confirmed):
                frappe.throw(
                    _("Confirm that you reviewed your profile and that it is current."),
                    frappe.ValidationError,
                )
            validate_profile_completeness(person, opportunity)


def get_external_person_for_user(user: str):
    if not user or user == "Guest":
        return None
    name = frappe.db.get_value("External Person", {"user": user}, "name")
    return frappe.get_doc("External Person", name) if name else None


def lock_and_get_opportunity(name: str):
    # Row lock prevents two requests from consuming the final place concurrently.
    locked = frappe.db.sql(
        "select name from `tabExternal Opportunity` where name=%s for update",
        name,
        as_dict=True,
    )
    if not locked:
        frappe.throw(_("External Opportunity {0} does not exist.").format(name))
    return frappe.get_doc("External Opportunity", name)


def _validate_opportunity_is_open(opportunity, current_application=None):
    if opportunity.status != "Published" or not cint(opportunity.publish_on_website):
        frappe.throw(_("Applications are closed for this opportunity."))
    if opportunity.opening_date and getdate(opportunity.opening_date) > getdate(today()):
        frappe.throw(_("Applications have not opened yet."))
    if opportunity.closing_date and getdate(opportunity.closing_date) < getdate(today()):
        frappe.throw(_("The application closing date has passed."))
    if opportunity.meta.has_field("allow_external_applications") and not cint(opportunity.allow_external_applications):
        frappe.throw(_("External applications are disabled for this opportunity."))

    limit = cint(opportunity.application_limit)
    if limit > 0:
        count = count_capacity_applications(opportunity.name, exclude_name=current_application)
        if count >= limit:
            frappe.throw(_("The application limit for this opportunity has been reached."))


def _validate_duplicate_application(doc):
    existing = frappe.db.sql(
        """
        select name
          from `tabParticipation Application`
         where opportunity = %s
           and external_person = %s
           and name != %s
           and coalesce(status, '') != 'Cancelled'
           and coalesce(final_decision, '') not in ('Withdrawn', 'Cancelled')
         limit 1
        """,
        (doc.opportunity, doc.external_person, doc.name or ""),
        as_dict=True,
    )
    if existing:
        frappe.throw(_("You already applied for this opportunity: {0}").format(existing[0].name))


def validate_profile_completeness(person, opportunity):
    missing = []
    for fieldname, label in (
        ("full_name", _("Full Name")),
        ("primary_email", _("Primary Email")),
        ("privacy_consent", _("Privacy Consent")),
    ):
        if person.meta.has_field(fieldname) and not person.get(fieldname):
            missing.append(label)

    if cint(opportunity.get("require_resume")) and person.meta.has_field("resume") and not person.resume:
        missing.append(_("Resume"))
    if missing:
        frappe.throw(
            _("Complete the following profile fields before applying: {0}").format(
                ", ".join(missing)
            )
        )


def get_participation_type(opportunity):
    explicit = opportunity.get("qorg_participation_type") or opportunity.get("participation_type")
    if explicit:
        return explicit
    opportunity_type = (opportunity.get("opportunity_type") or "").strip()
    if "intern" in opportunity_type.lower():
        return "Intern"
    return "Volunteer"


def count_capacity_applications(opportunity: str, exclude_name=None) -> int:
    conditions = ["opportunity = %s"]
    values = [opportunity]
    if exclude_name:
        conditions.append("name != %s")
        values.append(exclude_name)
    result = frappe.db.sql(
        f"""
        select count(*)
          from `tabParticipation Application`
         where {' and '.join(conditions)}
           and coalesce(status, '') != 'Cancelled'
           and coalesce(final_decision, '') not in ('Withdrawn', 'Cancelled')
        """,
        tuple(values),
    )
    return int(result[0][0] or 0)


def sync_opportunity_application_stats(opportunity_name: str | None):
    if not opportunity_name or not frappe.db.exists("External Opportunity", opportunity_name):
        return

    count = count_capacity_applications(opportunity_name)
    values = frappe.db.get_value(
        "External Opportunity",
        opportunity_name,
        ["application_limit", "close_at_application_limit", "status"],
        as_dict=True,
    )
    limit = cint(values.application_limit)
    remaining = max(limit - count, 0) if limit > 0 else 0
    updates = {
        "application_count": count,
        "remaining_application_capacity": remaining,
    }
    if limit > 0 and count >= limit and cint(values.close_at_application_limit):
        updates["status"] = "Closed"

    frappe.db.set_value(
        "External Opportunity",
        opportunity_name,
        updates,
        update_modified=False,
    )
    frappe.clear_document_cache("External Opportunity", opportunity_name)
    clear_website_cache()
