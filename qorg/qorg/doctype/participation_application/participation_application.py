from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, getdate, now_datetime, today
from frappe.website.utils import clear_cache as clear_website_cache

from qorg.qorg.volunteer_management import services

CAPACITY_EXCLUDED_STATUSES = {"Cancelled"}
CAPACITY_EXCLUDED_DECISIONS = {"Withdrawn", "Cancelled"}


class ParticipationApplication(Document):
    def before_validate(self):
        self._bind_portal_identity()

    def validate(self):
        self._validate_application_context()
        services.validate_application(self)

    def after_insert(self):
        sync_opportunity_application_stats(self.opportunity)

    def on_update(self):
        previous = self.get_doc_before_save()
        sync_opportunity_application_stats(self.opportunity)
        if previous and previous.opportunity != self.opportunity:
            sync_opportunity_application_stats(previous.opportunity)

    def on_trash(self):
        opportunity = self.opportunity
        if opportunity:
            frappe.db.after_commit.add(
                lambda opportunity=opportunity: sync_opportunity_application_stats(opportunity)
            )

    def _bind_portal_identity(self):
        if frappe.session.user == "Guest":
            frappe.throw(_("Please sign in before applying."), frappe.PermissionError)

        if not is_website_user(frappe.session.user):
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
        self.application_date = self.application_date or today()
        self.status = self.status or "Draft"

    def _validate_application_context(self):
        if not self.opportunity:
            frappe.throw(_("External Opportunity is required."))

        opportunity = lock_and_get_opportunity(self.opportunity)
        self.participation_type = get_participation_type(opportunity)
        self.application_date = self.application_date or today()
        self.status = self.status or "Draft"

        previous = self.get_doc_before_save()
        if self.is_new() or (previous and previous.opportunity != self.opportunity):
            validate_opportunity_is_open(opportunity, exclude_application=self.name)

        validate_duplicate_application(self)

        if is_website_user(frappe.session.user):
            person = get_external_person_for_user(frappe.session.user)
            if not person or person.name != self.external_person:
                frappe.throw(_("The application must use your own external profile."))
            if not cint(self.profile_review_confirmed):
                frappe.throw(
                    _("Confirm that you reviewed your profile and that it is current."),
                    frappe.ValidationError,
                )
            validate_profile_completeness(person, opportunity)


def is_website_user(user: str | None) -> bool:
    if not user or user == "Guest":
        return False
    return frappe.db.get_value("User", user, "user_type") == "Website User"


def get_external_person_for_user(user: str | None):
    if not user or user == "Guest" or not frappe.db.exists("DocType", "External Person"):
        return None
    name = frappe.db.get_value("External Person", {"user": user}, "name")
    return frappe.get_doc("External Person", name) if name else None


def lock_and_get_opportunity(name: str):
    locked = frappe.db.sql(
        "select name from `tabExternal Opportunity` where name=%s for update",
        name,
        as_dict=True,
    )
    if not locked:
        frappe.throw(_("External Opportunity {0} does not exist.").format(name))
    return frappe.get_doc("External Opportunity", name)


def validate_opportunity_is_open(opportunity, exclude_application=None):
    if opportunity.status != "Published" or not cint(opportunity.publish_on_website):
        frappe.throw(_("Applications are closed for this opportunity."))
    if opportunity.opening_date and getdate(opportunity.opening_date) > getdate(today()):
        frappe.throw(_("Applications have not opened yet."))
    if opportunity.closing_date and getdate(opportunity.closing_date) < getdate(today()):
        frappe.throw(_("The application closing date has passed."))
    if opportunity.meta.has_field("allow_external_applications") and not cint(
        opportunity.allow_external_applications
    ):
        frappe.throw(_("External applications are disabled for this opportunity."))

    limit = cint(opportunity.application_limit)
    if limit > 0 and count_capacity_applications(
        opportunity.name, exclude_name=exclude_application
    ) >= limit:
        frappe.throw(_("The application limit for this opportunity has been reached."))


def validate_duplicate_application(doc):
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

    if cint(opportunity.get("require_resume")):
        resume_field = next(
            (fieldname for fieldname in ("resume", "resume_attachment") if person.meta.has_field(fieldname)),
            None,
        )
        if resume_field and not person.get(resume_field):
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
    return "Intern" if "intern" in opportunity_type.lower() else "Volunteer"


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
    if not values:
        return

    limit = cint(values.application_limit)
    updates = {
        "application_count": count,
        "remaining_application_capacity": max(limit - count, 0) if limit > 0 else 0,
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
    frappe.db.after_commit.add(clear_website_cache)


def reconcile_all_opportunity_application_stats():
    if not frappe.db.exists("DocType", "External Opportunity") or not frappe.db.exists(
        "DocType", "Participation Application"
    ):
        return {"reconciled": 0}

    names = frappe.get_all("External Opportunity", pluck="name", limit_page_length=0)
    for name in names:
        sync_opportunity_application_stats(name)
    return {"reconciled": len(names)}
