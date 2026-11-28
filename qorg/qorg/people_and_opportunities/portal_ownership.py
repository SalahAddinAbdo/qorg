from __future__ import annotations

import frappe
from frappe import _

ACTIVE_STATUS = "Active"
BLOCKED_STATUSES = {"Inactive", "Deceased", "Do Not Contact", "Merged"}


def is_website_user(user: str | None = None) -> bool:
    user = user or frappe.session.user
    if user in (None, "", "Guest", "Administrator"):
        return False
    return frappe.db.get_value("User", user, "user_type") == "Website User"


def external_person_names_for_user(user: str | None = None) -> list[str]:
    user = user or frappe.session.user
    if not user or user == "Guest":
        return []
    return frappe.get_all(
        "External Person",
        filters={"user": user},
        pluck="name",
        order_by="creation asc",
        limit_page_length=0,
    )


def get_external_person_for_user(
    user: str | None = None,
    *,
    required: bool = False,
    active_only: bool = False,
):
    user = user or frappe.session.user
    if not user or user == "Guest":
        if required:
            frappe.throw(_("Please sign in before continuing."), frappe.PermissionError)
        return None

    names = external_person_names_for_user(user)
    if len(names) > 1:
        frappe.throw(
            _("More than one External Person is linked to this user. An administrator must reconcile the records."),
            frappe.ValidationError,
        )
    if not names:
        if required:
            frappe.throw(_("Create your external profile before continuing."), frappe.ValidationError)
        return None

    doc = frappe.get_doc("External Person", names[0])
    if active_only and doc.person_status != ACTIVE_STATUS:
        frappe.throw(
            _("The external profile is not active and cannot be used for a new application."),
            frappe.PermissionError,
        )
    return doc


def can_access_external_person(doc, user: str | None = None, permission_type: str = "read"):
    user = user or frappe.session.user
    if user == "Administrator":
        return True
    if not is_website_user(user):
        # Frappe v16 requires an explicit truthy result from has_permission hooks.
        # Role Permission Manager and User Permissions are evaluated afterwards.
        return True
    if permission_type in {"create"}:
        return not external_person_names_for_user(user)
    return bool(doc and doc.get("user") == user)


def assert_owned_external_person(name: str | None, *, active_only: bool = False):
    person = get_external_person_for_user(required=True, active_only=active_only)
    if name and person.name != name:
        frappe.throw(_("The selected external profile is not owned by the current user."), frappe.PermissionError)
    return person


def portal_owned_reference(doctype: str, name: str, user: str | None = None) -> bool:
    user = user or frappe.session.user
    if user == "Administrator":
        return True
    if not is_website_user(user):
        return False
    person = get_external_person_for_user(user=user)
    if not person:
        return False
    if doctype == "External Person":
        return name == person.name
    meta = frappe.get_meta(doctype)
    for fieldname in ("external_person", "qorg_external_person"):
        if meta.has_field(fieldname):
            return frappe.db.get_value(doctype, name, fieldname) == person.name
    return False
