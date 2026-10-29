from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint

from qorg.qorg.people_and_opportunities.web_form_design import (
    reconcile_all_web_form_designs,
    validate_website_settings as validate_web_form_design_settings,
)

PORTAL_ROLE = "External Applicant"

DEFAULTS = {
    "enabled": 1,
    "public_listing": 1,
    "applications_enabled": 1,
    "default_visibility": "Public",
    "show_upcoming": 0,
    "show_closed": 1,
    "page_size": 24,
}


def get_opportunity_portal_settings():
    values = frappe._dict(DEFAULTS.copy())
    if not frappe.db.exists("DocType", "Website Settings"):
        return values
    settings = frappe.get_single("Website Settings")
    mapping = {
        "enabled": "qorg_opportunity_portal_enabled",
        "public_listing": "qorg_public_opportunity_listing",
        "applications_enabled": "qorg_external_applications_enabled",
        "default_visibility": "qorg_default_opportunity_visibility",
        "show_upcoming": "qorg_show_upcoming_opportunities",
        "show_closed": "qorg_show_closed_opportunities",
        "page_size": "qorg_opportunity_portal_page_size",
    }
    for key, fieldname in mapping.items():
        if settings.meta.has_field(fieldname) and settings.get(fieldname) is not None:
            values[key] = settings.get(fieldname)
    values.enabled = cint(values.enabled)
    values.public_listing = cint(values.public_listing)
    values.applications_enabled = cint(values.applications_enabled)
    values.show_upcoming = cint(values.show_upcoming)
    values.show_closed = cint(values.show_closed)
    values.page_size = min(max(cint(values.page_size) or 24, 6), 50)
    values.default_visibility = values.default_visibility or "Public"
    return values


def validate_website_settings(doc, method=None):
    if doc.meta.has_field("qorg_opportunity_portal_page_size"):
        size = cint(doc.get("qorg_opportunity_portal_page_size") or 24)
        if size < 6 or size > 50:
            frappe.throw(_("Opportunities per Page must be between 6 and 50."))
    validate_web_form_design_settings(doc, method)


def reconcile_web_form_designs(doc, method=None):
    reconcile_all_web_form_designs(doc, method)


def sync_external_person_portal_access(doc, method=None):
    if not doc.meta.has_field("user") or not doc.get("user"):
        return
    if not frappe.db.exists("User", doc.user):
        return
    user_type, enabled = frappe.db.get_value(
        "User", doc.user, ["user_type", "enabled"]
    ) or (None, None)
    if not enabled or user_type != "Website User":
        return
    _ensure_role()
    user = frappe.get_doc("User", doc.user)
    if PORTAL_ROLE not in {row.role for row in user.get("roles") or []}:
        user.append("roles", {"role": PORTAL_ROLE})
        user.flags.ignore_permissions = True
        user.save()


def provision_portal_role_and_menu():
    _ensure_role()
    try:
        from frappe.website.doctype.portal_settings.portal_settings import sync_menu

        sync_menu()
    except (ImportError, AttributeError):
        frappe.log_error(
            title="Opportunity Portal Menu Sync",
            message="Portal Settings sync_menu is unavailable. Reset Portal Settings manually.",
        )


def _ensure_role():
    if not frappe.db.exists("Role", PORTAL_ROLE):
        frappe.get_doc(
            {
                "doctype": "Role",
                "role_name": PORTAL_ROLE,
                "desk_access": 0,
                "is_custom": 0,
            }
        ).insert(ignore_permissions=True)
