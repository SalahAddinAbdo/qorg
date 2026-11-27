from __future__ import annotations

from datetime import date

import frappe
from frappe import _
from frappe.utils import flt, getdate, today


def _age_on(birth_date, on_date=None):
    born = getdate(birth_date)
    current = getdate(on_date or today())
    if born > current:
        frappe.throw(_("Date of Birth cannot be in the future."))
    return current.year - born.year - ((current.month, current.day) < (born.month, born.day))


def _text(value):
    return " ".join(str(value or "").casefold().split())


def _contains_requirement(rows, fields, requirement):
    required = _text(requirement)
    if not required:
        return bool(rows)
    return any(required in _text(" ".join(str(row.get(field) or "") for field in fields)) for row in rows)


def _experience_years(rows):
    days = 0
    current = getdate(today())
    for row in rows:
        if not row.get("from_date"):
            continue
        start = getdate(row.from_date)
        end = current if row.get("currently_working") or not row.get("to_date") else getdate(row.to_date)
        if end >= start:
            days += (end - start).days + 1
    return days / 365.25


def _requirement_satisfied(person, row):
    requirement = row.get("requirement")
    minimum = flt(row.get("minimum_value"))
    maximum = flt(row.get("maximum_value"))
    kind = row.get("requirement_type")
    if kind == "Education":
        return _contains_requirement(person.get("education") or [], ("qualification", "field_of_study", "institution"), requirement)
    if kind == "Experience":
        rows = person.get("experience") or []
        if not _contains_requirement(rows, ("organization", "job_title", "project_or_program", "sector", "responsibilities"), requirement):
            return False
        years = _experience_years(rows)
        return (not minimum or years >= minimum) and (not maximum or years <= maximum)
    if kind == "Skill":
        rows = [r for r in (person.get("skills") or []) if not requirement or _text(requirement) in _text(r.get("skill"))]
        if not rows:
            return False
        return not minimum or max(flt(r.get("years_of_experience")) for r in rows) >= minimum
    if kind == "Language":
        return _contains_requirement(person.get("languages") or [], ("language", "reading", "writing", "speaking"), requirement)
    if kind == "Certification":
        return _contains_requirement(person.get("training") or [], ("course_title", "provider", "certificate_number"), requirement)
    if kind == "Availability":
        return True
    return bool(requirement)


def missing_profile_requirements(person, opportunity):
    missing = []
    if not person.full_name:
        missing.append(_("Full Name"))
    if not (person.primary_email or person.mobile_no):
        missing.append(_("Email or Mobile Number"))
    minimum_age = int(opportunity.get("minimum_age") or 0)
    maximum_age = int(opportunity.get("maximum_age") or 0)
    if minimum_age or maximum_age:
        if not person.get("date_of_birth"):
            missing.append(_("Date of Birth"))
        else:
            age = _age_on(person.date_of_birth)
            if minimum_age and age < minimum_age:
                missing.append(_("Minimum Age"))
            if maximum_age and age > maximum_age:
                missing.append(_("Maximum Age"))
    if opportunity.get("require_resume") and not person.get("resume"):
        missing.append(_("Resume"))
    if opportunity.get("require_identification") and not (
        person.get("identification_type")
        and person.get("identification_number")
        and person.get("identification_country")
    ):
        missing.append(_("Identification Details"))
    for row in opportunity.get("requirements") or []:
        if row.get("is_mandatory") and not _requirement_satisfied(person, row):
            missing.append(row.get("requirement") or row.get("requirement_type"))
    return list(dict.fromkeys(missing))


def validate_profile_for_opportunity(person, opportunity):
    missing = missing_profile_requirements(person, opportunity)
    if missing:
        frappe.throw(
            _("Complete the following profile requirements before applying: {0}").format(", ".join(missing))
        )
    return True
