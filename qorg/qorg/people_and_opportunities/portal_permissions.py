from __future__ import annotations

import frappe

from qorg.qorg.people_and_opportunities.portal_ownership import (
    can_access_external_person,
    get_external_person_for_user,
    is_website_user,
)


def external_person_query(user=None):
    user = user or frappe.session.user
    if not is_website_user(user):
        return ""
    return "`tabExternal Person`.`user` = {0}".format(frappe.db.escape(user))


def external_person_permission(doc, user=None, permission_type=None):
    return can_access_external_person(doc, user=user, permission_type=permission_type or "read")


def participation_application_query(user=None):
    user = user or frappe.session.user
    if not is_website_user(user):
        return ""
    person = get_external_person_for_user(user=user)
    if not person:
        return "1=0"
    return "`tabParticipation Application`.`external_person` = {0}".format(
        frappe.db.escape(person.name)
    )


def participation_application_permission(doc, user=None, permission_type=None):
    user = user or frappe.session.user
    if not is_website_user(user):
        return None
    person = get_external_person_for_user(user=user)
    if permission_type == "create":
        return bool(person and person.person_status == "Active")
    return bool(person and doc.get("external_person") == person.name)


def job_applicant_query(user=None):
    user = user or frappe.session.user
    if not is_website_user(user):
        return ""
    person = get_external_person_for_user(user=user)
    if not person:
        return "1=0"
    return "`tabJob Applicant`.`qorg_external_person` = {0}".format(
        frappe.db.escape(person.name)
    )


def job_applicant_permission(doc, user=None, permission_type=None):
    user = user or frappe.session.user
    if not is_website_user(user):
        return None
    person = get_external_person_for_user(user=user)
    if permission_type == "create":
        return bool(person and person.person_status == "Active")
    return bool(person and doc.get("qorg_external_person") == person.name)
