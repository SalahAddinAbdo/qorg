from __future__ import annotations

import frappe
from qorg.qorg.people_and_opportunities.settings import settings
from frappe.utils import cint


def _owned_profile(name: str):
    if frappe.session.user == "Guest":
        frappe.throw("Login required", frappe.PermissionError)
    doc = frappe.get_doc("External Person", name)
    if doc.user != frappe.session.user and frappe.session.user != "Administrator":
        frappe.throw("Not permitted", frappe.PermissionError)
    return doc


@frappe.whitelist()
def get_profile(name: str):
    doc = _owned_profile(name)
    return {
        "name": doc.name,
        "full_name": doc.full_name,
        "name_in_arabic": doc.name_in_arabic,
        "professional_title": doc.professional_title,
        "professional_summary": doc.professional_summary,
        "career_objective": doc.career_objective,
        "primary_email": doc.primary_email,
        "secondary_email": doc.secondary_email,
        "mobile_no": doc.mobile_no,
        "alternative_mobile_no": doc.alternative_mobile_no,
        "preferred_language": doc.preferred_language,
        "preferred_contact_method": doc.preferred_contact_method,
        "portfolio_url": doc.portfolio_url,
        "linkedin_url": doc.linkedin_url,
        "profile_completion": doc.profile_completion,
        "last_profile_update": doc.last_profile_update,
        "education_count": len(doc.education or []),
        "experience_count": len(doc.experience or []),
        "training_count": len(doc.training or []),
        "language_count": len(doc.languages or []),
        "skill_count": len(doc.skills or []),
    }


@frappe.whitelist(methods=["POST"])
def update_profile(name: str, values):
    if not settings().allow_profile_web_update:
        frappe.throw("Web profile updates are disabled.", frappe.PermissionError)
    doc = _owned_profile(name)
    values = frappe.parse_json(values) or {}
    allowed = {
        "full_name",
        "name_in_arabic",
        "professional_title",
        "professional_summary",
        "career_objective",
        "primary_email",
        "secondary_email",
        "mobile_no",
        "alternative_mobile_no",
        "preferred_language",
        "preferred_contact_method",
        "portfolio_url",
        "linkedin_url",
    }
    for fieldname in allowed:
        if fieldname in values:
            doc.set(fieldname, values.get(fieldname))
    doc.flags.ignore_permissions = True
    doc.save()
    return get_profile(doc.name)
