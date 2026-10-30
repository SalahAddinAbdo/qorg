from __future__ import annotations

import re
from datetime import date
from urllib.parse import quote

import frappe
from frappe import _
from frappe.website.utils import clear_cache as clear_website_cache
from frappe.utils import cint, getdate, now_datetime, today

from qorg.qorg.people_and_opportunities.portal_settings import (
    get_opportunity_portal_settings,
)

PUBLIC_SCALAR_FIELDS = (
    "name",
    "opportunity_title",
    "opportunity_type",
    "company",
    "status",
    "opening_date",
    "closing_date",
    "expected_start_date",
    "expected_end_date",
    "work_arrangement",
    "employment_type",
    "duration_text",
    "summary",
    "description",
    "responsibilities",
    "qualifications",
    "selection_process",
    "application_instructions",
    "application_limit",
    "public_contact_email",
    "route",
    "project",
    "department",
    "designation",
    "participation_type",
    "number_of_positions",
    "minimum_age",
    "expected_total_hours",
    "stipend_allowance_policy",
    "allow_external_applications",
    "require_portal_account",
    "require_resume",
    "require_cover_letter",
    "require_identification",
)

PUBLIC_CHILD_FIELDS = {
    "Opportunity Location": (
        "country",
        "governorate",
        "district",
        "location",
        "location_details",
        "is_primary",
        "vacancy_count",
    ),
    "Opportunity Requirement": (
        "requirement_type",
        "requirement",
        "is_mandatory",
        "minimum_value",
        "maximum_value",
        "notes",
    ),
    "Opportunity Screening Question": (
        "question",
        "answer_type",
        "options",
        "is_mandatory",
        "display_order",
    ),
}

FINAL_OR_INELIGIBLE_APPLICATION_STATUSES = {
    "Rejected",
    "Withdrawn",
    "Disqualified",
    "Cancelled",
    "Closed",
}



def validate_external_opportunity_publication(doc, method=None):
    settings = get_opportunity_portal_settings()
    if _has_field(doc, "portal_visibility") and not doc.get("portal_visibility"):
        doc.portal_visibility = settings.default_visibility
    if not cint(doc.get("publish_on_website")) and doc.get("status") != "Published":
        return

    if doc.get("status") == "Published" and not cint(doc.get("publish_on_website")):
        frappe.throw(_("Enable Publish on Website before setting the status to Published."))

    if not cint(doc.get("publish_on_website")):
        return

    missing = []
    for fieldname, label in (
        ("opportunity_title", _("Opportunity Title")),
        ("opportunity_type", _("Opportunity Type")),
        ("company", _("Company")),
        ("opening_date", _("Opening Date")),
        ("summary", _("Summary")),
        ("description", _("Description")),
    ):
        if _has_field(doc, fieldname) and not doc.get(fieldname):
            missing.append(label)

    if missing:
        frappe.throw(
            _("Complete the following public fields before publication: {0}").format(
                ", ".join(missing)
            )
        )

    if doc.get("opening_date") and doc.get("closing_date"):
        if getdate(doc.opening_date) > getdate(doc.closing_date):
            frappe.throw(_("Closing Date cannot be before Opening Date."))

    if _has_field(doc, "allow_external_applications") and not cint(
        doc.get("allow_external_applications")
    ):
        frappe.throw(_("Enable external applications before publishing this opportunity."))

    ensure_public_route(doc)

    if doc.get("status") == "Published":
        if _has_field(doc, "published_on") and not doc.get("published_on"):
            doc.published_on = now_datetime()
        if _has_field(doc, "published_by") and not doc.get("published_by"):
            doc.published_by = frappe.session.user


def handle_external_opportunity_publication(doc, method=None):
    if doc.get("status") == "Published" and cint(doc.get("publish_on_website")):
        ensure_public_route(doc)
    clear_website_cache()


def ensure_public_route(doc):
    if not _has_field(doc, "route"):
        return None
    current = (doc.get("route") or "").strip().strip("/")
    if current:
        _assert_unique_route(doc.name, current)
        return current

    base = _slugify(doc.get("opportunity_title") or doc.name)
    candidate = base
    index = 2
    while frappe.db.exists(
        "External Opportunity", {"route": candidate, "name": ["!=", doc.name]}
    ):
        candidate = f"{base}-{index}"
        index += 1
    doc.route = candidate
    return candidate


def get_public_opportunities(filters=None, limit_start=0, limit_page_length=None):
    settings = get_opportunity_portal_settings()
    if not settings.enabled:
        return []
    filters = frappe._dict(filters or {})
    limit_page_length = min(
        max(cint(limit_page_length) or settings.page_size, 6), 50
    )
    limit_start = max(cint(limit_start), 0)

    allowed_statuses = ["Published"]
    if settings.show_closed:
        allowed_statuses.append("Closed")
    query_filters = {
        "status": ["in", allowed_statuses],
        "publish_on_website": 1,
    }
    if not settings.show_upcoming:
        query_filters["opening_date"] = ["<=", today()]
    if _meta_has_field("External Opportunity", "portal_visibility"):
        allowed = []
        if settings.public_listing:
            allowed.append("Public")
        if frappe.session.user != "Guest":
            allowed.append("Authenticated Users")
        if not allowed:
            return []
        query_filters["portal_visibility"] = ["in", allowed]

    fields = _existing_fields("External Opportunity", PUBLIC_SCALAR_FIELDS)
    opportunities = frappe.get_all(
        "External Opportunity",
        filters=query_filters,
        fields=fields,
        order_by="is_featured desc, closing_date asc, opening_date desc"
        if _meta_has_field("External Opportunity", "is_featured")
        else "closing_date asc, opening_date desc",
        limit_start=limit_start,
        limit_page_length=limit_page_length,
    )
    normalized = [_normalize_public_opportunity(row) for row in opportunities]
    if not settings.show_closed:
        normalized = [row for row in normalized if row.get("is_open")]
    if not settings.show_upcoming:
        normalized = [
            row for row in normalized
            if not row.get("opening_date") or getdate(row.opening_date) <= getdate(today())
        ]
    search_text = frappe.as_unicode(filters.get("search") or "").strip().lower()
    type_filter = frappe.as_unicode(filters.get("type") or "").strip()
    arrangement_filter = frappe.as_unicode(filters.get("arrangement") or "").strip()
    if search_text:
        normalized = [
            row for row in normalized
            if search_text in frappe.as_unicode(row.get("opportunity_title") or "").lower()
            or search_text in frappe.as_unicode(row.get("summary") or "").lower()
        ]
    if type_filter:
        normalized = [
            row for row in normalized
            if row.get("opportunity_type") == type_filter
            or row.get("participation_type") == type_filter
        ]
    if arrangement_filter:
        normalized = [
            row for row in normalized
            if row.get("work_arrangement") == arrangement_filter
        ]
    return normalized


def get_public_opportunity(route):
    settings = get_opportunity_portal_settings()
    if not settings.enabled:
        raise frappe.DoesNotExistError
    route = (route or "").strip().strip("/")
    if not route:
        raise frappe.DoesNotExistError
    filters = {"route": route, "publish_on_website": 1}
    name = frappe.db.get_value("External Opportunity", filters, "name")
    if not name:
        raise frappe.DoesNotExistError
    doc = frappe.get_doc("External Opportunity", name)
    if doc.get("status") not in ("Published", "Closed"):
        raise frappe.DoesNotExistError
    if doc.get("status") == "Closed" and not settings.show_closed:
        raise frappe.DoesNotExistError
    if (
        doc.get("opening_date")
        and getdate(doc.opening_date) > getdate(today())
        and not settings.show_upcoming
    ):
        raise frappe.DoesNotExistError
    if not _viewer_can_see(doc):
        raise frappe.PermissionError
    result = _sanitize_doc(doc)
    result["is_open"] = is_opportunity_open(doc)
    behavior = _opportunity_behavior(doc)
    if behavior == "Employment":
        result["apply_url"] = f"/employment-application/new?external_opportunity={quote(doc.name)}"
    else:
        result["apply_url"] = f"/participation-application/new?opportunity={quote(doc.name)}"
    return result


def is_opportunity_open(doc):
    if doc.get("status") != "Published":
        return False
    if not cint(doc.get("publish_on_website")):
        return False
    if doc.get("opening_date") and getdate(doc.opening_date) > getdate(today()):
        return False
    if doc.get("closing_date") and getdate(doc.closing_date) < getdate(today()):
        return False
    if _has_field(doc, "allow_external_applications") and not cint(
        doc.get("allow_external_applications")
    ):
        return False
    limit = cint(doc.get("application_limit"))
    if limit > 0:
        from qorg.qorg.doctype.participation_application.participation_application import (
            count_capacity_applications,
        )
        if count_capacity_applications(doc.name) >= limit:
            return False
    return True


@frappe.whitelist()
def submit_opportunity_application(
    opportunity_route,
    motivation=None,
    availability_start_date=None,
    hours_per_week=None,
    consent=None,
):
    settings = get_opportunity_portal_settings()
    if not settings.enabled or not settings.applications_enabled:
        frappe.throw(_("External applications are currently disabled."))
    if frappe.session.user == "Guest":
        frappe.throw(_("Please sign in before applying."), frappe.PermissionError)
    if not cint(consent):
        frappe.throw(_("Confirm that you reviewed your profile and that it is current."))

    public = get_public_opportunity(opportunity_route)
    doc = frappe.get_doc("External Opportunity", public.name)
    if not is_opportunity_open(doc):
        frappe.throw(_("Applications are closed for this opportunity."))

    person = _get_external_person_for_user(frappe.session.user)
    if not person:
        frappe.throw(
            _("Complete your external profile before applying. Open /external-profile."),
            frappe.ValidationError,
        )

    behavior = _opportunity_behavior(doc)
    if behavior == "Employment":
        application = _create_job_applicant(doc, person, motivation)
    else:
        application = _create_participation_application(
            doc,
            person,
            motivation,
            availability_start_date,
            hours_per_week,
        )

    return {
        "ok": True,
        "doctype": application.doctype,
        "name": application.name,
        "message": _("Your application has been submitted successfully."),
    }


@frappe.whitelist()
def get_my_applications():
    if frappe.session.user == "Guest":
        frappe.throw(_("Please sign in to view your applications."), frappe.PermissionError)
    person = _get_external_person_for_user(frappe.session.user)
    if not person:
        return []
    rows = []
    rows.extend(_get_participation_applications(person.name))
    rows.extend(_get_job_applications(person.name, person.get("primary_email")))
    rows.sort(key=lambda row: str(row.get("application_date") or ""), reverse=True)
    return rows


def close_expired_opportunities():
    names = frappe.get_all(
        "External Opportunity",
        filters={
            "status": "Published",
            "publish_on_website": 1,
            "closing_date": ["<", today()],
        },
        pluck="name",
    )
    for name in names:
        frappe.db.set_value(
            "External Opportunity",
            name,
            "status",
            "Closed",
            update_modified=True,
        )
    if names:
        clear_website_cache()
    return {"closed": len(names)}


def _create_participation_application(
    opportunity, person, motivation, availability_start_date, hours_per_week
):
    if not frappe.db.exists("DocType", "Participation Application"):
        frappe.throw(_("Participation Application is not installed."))
    duplicate_filters = {
        "external_person": person.name,
        "opportunity": opportunity.name,
    }
    existing = frappe.db.get_value(
        "Participation Application",
        duplicate_filters,
        ["name", "status"],
        as_dict=True,
    )
    if existing and existing.status not in FINAL_OR_INELIGIBLE_APPLICATION_STATUSES:
        frappe.throw(
            _("You already have an active application for this opportunity: {0}").format(
                existing.name
            )
        )

    target = frappe.new_doc("Participation Application")
    _set_if_field(target, "external_person", person.name)
    _set_if_field(target, "opportunity", opportunity.name)
    _set_if_field(target, "company", opportunity.get("company"))
    _set_if_field(target, "project", opportunity.get("project"))
    _set_if_field(target, "branch", opportunity.get("branch"))
    _set_if_field(target, "application_date", today())
    _set_if_field(target, "application_source", "Portal")
    _set_if_field(target, "status", "Submitted")
    _set_if_field(target, "applicant_name", person.get("full_name"))
    _set_if_field(target, "email", person.get("primary_email"))
    _set_if_field(target, "mobile_no", person.get("mobile_no"))
    _set_if_field(target, "motivation", motivation)
    _set_if_field(target, "availability_start_date", availability_start_date)
    _set_if_field(target, "hours_per_week", hours_per_week)
    _set_if_field(target, "participation_type", _participation_type(opportunity))
    _set_if_field(target, "profile_review_confirmed", 1)
    _set_if_field(target, "profile_reviewed_by", frappe.session.user)
    _set_if_field(target, "profile_reviewed_on", now_datetime())
    _set_if_field(target, "profile_modified_on_application", person.modified)
    target.insert(ignore_permissions=True)
    return target


def _create_job_applicant(opportunity, person, motivation):
    if not opportunity.get("job_opening"):
        frappe.throw(_("The employment opportunity is not linked to a Job Opening."))
    email = person.get("primary_email")
    duplicate = None
    meta = frappe.get_meta("Job Applicant")
    if meta.has_field("qorg_external_opportunity") and meta.has_field("qorg_external_person"):
        duplicate = frappe.db.get_value(
            "Job Applicant",
            {
                "qorg_external_opportunity": opportunity.name,
                "qorg_external_person": person.name,
            },
            "name",
        )
    elif email:
        duplicate = frappe.db.get_value(
            "Job Applicant",
            {"job_title": opportunity.job_opening, "email_id": email},
            "name",
        )
    if duplicate:
        frappe.throw(_("You already applied for this opportunity: {0}").format(duplicate))

    target = frappe.new_doc("Job Applicant")
    _set_if_field(target, "applicant_name", person.get("full_name"))
    _set_if_field(target, "email_id", email)
    _set_if_field(target, "phone_number", person.get("mobile_no"))
    _set_if_field(target, "job_title", opportunity.get("job_opening"))
    _set_if_field(target, "status", "Open")
    _set_if_field(target, "source", "Portal")
    _set_if_field(target, "cover_letter", motivation)
    _set_if_field(target, "qorg_external_person", person.name)
    _set_if_field(target, "qorg_external_opportunity", opportunity.name)
    _copy_attachment(person, target, "resume", ("resume_attachment", "resume"))
    target.insert(ignore_permissions=True)
    return target


def _get_participation_applications(person_name):
    if not frappe.db.exists("DocType", "Participation Application"):
        return []
    meta = frappe.get_meta("Participation Application")
    fields = ["name", "modified"]
    for fieldname in (
        "opportunity",
        "status",
        "application_date",
        "final_decision",
        "overall_score",
    ):
        if meta.has_field(fieldname):
            fields.append(fieldname)
    rows = frappe.get_all(
        "Participation Application",
        filters={"external_person": person_name},
        fields=fields,
        order_by="modified desc",
    )
    return [
        {
            "doctype": "Participation Application",
            "name": row.name,
            "opportunity": row.get("opportunity"),
            "status": row.get("status") or row.get("final_decision"),
            "application_date": row.get("application_date") or row.modified,
            "overall_score": row.get("overall_score"),
        }
        for row in rows
    ]


def _get_job_applications(person_name, email):
    if not frappe.db.exists("DocType", "Job Applicant"):
        return []
    meta = frappe.get_meta("Job Applicant")
    filters = {}
    if meta.has_field("qorg_external_person"):
        filters["qorg_external_person"] = person_name
    elif email:
        filters["email_id"] = email
    else:
        return []
    fields = ["name", "modified", "status", "job_title"]
    for fieldname in ("qorg_external_opportunity", "qorg_overall_score"):
        if meta.has_field(fieldname):
            fields.append(fieldname)
    rows = frappe.get_all(
        "Job Applicant",
        filters=filters,
        fields=fields,
        order_by="modified desc",
    )
    return [
        {
            "doctype": "Job Applicant",
            "name": row.name,
            "opportunity": row.get("qorg_external_opportunity") or row.get("job_title"),
            "status": row.get("status"),
            "application_date": row.modified,
            "overall_score": row.get("qorg_overall_score"),
        }
        for row in rows
    ]


def _get_external_person_for_user(user):
    if not frappe.db.exists("DocType", "External Person"):
        return None
    meta = frappe.get_meta("External Person")
    if not meta.has_field("user"):
        return None
    name = frappe.db.get_value("External Person", {"user": user}, "name")
    return frappe.get_doc("External Person", name) if name else None


def _viewer_can_see(doc):
    visibility = doc.get("portal_visibility") or "Public"
    if visibility == "Internal Only":
        return (
            frappe.session.user != "Guest"
            and frappe.db.get_value("User", frappe.session.user, "user_type") == "System User"
        )
    if visibility == "Authenticated Users":
        return frappe.session.user != "Guest"
    return True


def _sanitize_doc(doc):
    result = frappe._dict()
    for fieldname in PUBLIC_SCALAR_FIELDS:
        if _has_field(doc, fieldname):
            result[fieldname] = doc.get(fieldname)
    meta = frappe.get_meta(doc.doctype)
    result.sections = []
    for field in meta.fields:
        if field.fieldtype != "Table" or field.options not in PUBLIC_CHILD_FIELDS:
            continue
        allowed = PUBLIC_CHILD_FIELDS[field.options]
        rows = []
        for row in doc.get(field.fieldname) or []:
            rows.append({name: row.get(name) for name in allowed if row.meta.has_field(name)})
        if rows:
            result.sections.append(
                {"fieldname": field.fieldname, "label": field.label, "rows": rows}
            )
    return result


def _normalize_public_opportunity(row):
    row = frappe._dict(row)
    row["is_open"] = (
        row.get("status") == "Published"
        and (not row.get("opening_date") or getdate(row.opening_date) <= getdate(today()))
        and (not row.get("closing_date") or getdate(row.closing_date) >= getdate(today()))
    )
    if row.get("closing_date"):
        row["days_remaining"] = (getdate(row.closing_date) - getdate(today())).days
    else:
        row["days_remaining"] = None
    return row


def _opportunity_behavior(doc):
    opportunity_type = doc.get("opportunity_type")
    if not opportunity_type:
        return doc.get("participation_type") or "Other"
    if frappe.db.exists("DocType", "External Opportunity Type"):
        behavior = frappe.db.get_value(
            "External Opportunity Type", opportunity_type, "behavior_code"
        )
        if behavior:
            return behavior
    return opportunity_type


def _participation_type(doc):
    explicit = doc.get("participation_type")
    if explicit:
        return explicit
    behavior = _opportunity_behavior(doc)
    return "Intern" if behavior == "Internship" else "Volunteer"


def _existing_fields(doctype, names):
    meta = frappe.get_meta(doctype)
    return [name for name in names if name == "name" or meta.has_field(name)]


def _meta_has_field(doctype, fieldname):
    return frappe.get_meta(doctype).has_field(fieldname)


def _has_field(doc, fieldname):
    return doc.meta.has_field(fieldname)


def _set_if_field(doc, fieldname, value):
    if value is not None and doc.meta.has_field(fieldname):
        doc.set(fieldname, value)


def _copy_attachment(source, target, source_field, target_fields):
    value = source.get(source_field) if source.meta.has_field(source_field) else None
    if not value:
        return
    for fieldname in target_fields:
        if target.meta.has_field(fieldname):
            target.set(fieldname, value)
            return


def _slugify(value):
    value = frappe.as_unicode(value or "").strip().lower()
    value = re.sub(r"[^a-z0-9\u0600-\u06ff]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "opportunity"


def _assert_unique_route(name, route):
    duplicate = frappe.db.get_value(
        "External Opportunity", {"route": route, "name": ["!=", name]}, "name"
    )
    if duplicate:
        frappe.throw(_("Public Route is already used by opportunity {0}.").format(duplicate))
