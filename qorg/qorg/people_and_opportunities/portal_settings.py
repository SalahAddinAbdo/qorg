from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint

from qorg.qorg.people_and_opportunities.web_form_design import (
    reconcile_all_web_form_designs,
    validate_website_settings as validate_web_form_design_settings,
)

PORTAL_ROLE = "External Applicant"

SETTING_FIELD_MAP = {
    "enabled": "qorg_opportunity_portal_enabled",
    "public_listing": "qorg_public_opportunity_listing",
    "applications_enabled": "qorg_external_applications_enabled",
    "default_visibility": "qorg_default_opportunity_visibility",
    "show_upcoming": "qorg_show_upcoming_opportunities",
    "show_closed": "qorg_show_closed_opportunities",
    "page_size": "qorg_opportunity_portal_page_size",
}

PAGE_SIZE_MIN = 6
PAGE_SIZE_MAX = 50
SAFE_DEFAULT_VISIBILITY = "Internal Only"
SAFE_DEFAULT_PAGE_SIZE = 24


def get_opportunity_portal_settings():
    if not frappe.db.exists("DocType", "Website Settings"):
        frappe.throw(_("Website Settings is required for the opportunity portal."))

    settings = frappe.get_single("Website Settings")
    missing_fields = [
        fieldname
        for fieldname in SETTING_FIELD_MAP.values()
        if not settings.meta.has_field(fieldname)
    ]
    if missing_fields:
        frappe.throw(
            _("Opportunity Portal settings are not provisioned: {0}").format(
                ", ".join(missing_fields)
            )
        )

    values = frappe._dict(
        {key: settings.get(fieldname) for key, fieldname in SETTING_FIELD_MAP.items()}
    )
    values.enabled = cint(values.enabled)
    values.public_listing = cint(values.public_listing)
    values.applications_enabled = cint(values.applications_enabled)
    values.show_upcoming = cint(values.show_upcoming)
    values.show_closed = cint(values.show_closed)
    values.default_visibility = (
        values.default_visibility or SAFE_DEFAULT_VISIBILITY
    ).strip()
    values.page_size = cint(values.page_size or SAFE_DEFAULT_PAGE_SIZE)

    if not PAGE_SIZE_MIN <= values.page_size <= PAGE_SIZE_MAX:
        frappe.throw(
            _("Opportunities per Page must be between {0} and {1}.").format(
                PAGE_SIZE_MIN, PAGE_SIZE_MAX
            )
        )
    return values


def validate_website_settings(doc, method=None):
    if doc.meta.has_field("qorg_opportunity_portal_page_size"):
        size = cint(doc.get("qorg_opportunity_portal_page_size"))
        if size < PAGE_SIZE_MIN or size > PAGE_SIZE_MAX:
            frappe.throw(
                _("Opportunities per Page must be between {0} and {1}.").format(
                    PAGE_SIZE_MIN, PAGE_SIZE_MAX
                )
            )
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
