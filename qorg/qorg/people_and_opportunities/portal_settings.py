from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint
from frappe.website.utils import delete_page_cache

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

WEB_FORM_DESIGN_DEFAULTS = {
    "enabled": 1,
    "use_company_branding": 1,
    "default_company": None,
    "show_hero_header": 1,
    "show_privacy_notice": 1,
    "sticky_actions": 1,
    "hide_child_row_name": 1,
    "max_content_width": 1180,
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

    if doc.meta.has_field("qorg_web_form_max_content_width"):
        width = cint(doc.get("qorg_web_form_max_content_width") or 1180)
        if width < 760 or width > 1600:
            frappe.throw(_("Web Form Maximum Content Width must be between 760 and 1600 pixels."))

    delete_page_cache()


@frappe.whitelist(allow_guest=True)
def get_web_form_design_settings(route=None):
    values = frappe._dict(WEB_FORM_DESIGN_DEFAULTS.copy())
    if not frappe.db.exists("DocType", "Website Settings"):
        return values

    settings = frappe.get_single("Website Settings")
    mapping = {
        "enabled": "qorg_enable_enhanced_web_form_design",
        "use_company_branding": "qorg_web_form_use_company_branding",
        "default_company": "qorg_web_form_default_company",
        "show_hero_header": "qorg_web_form_show_hero_header",
        "show_privacy_notice": "qorg_web_form_show_privacy_notice",
        "sticky_actions": "qorg_web_form_sticky_actions",
        "hide_child_row_name": "qorg_web_form_hide_child_row_name",
        "max_content_width": "qorg_web_form_max_content_width",
    }
    for key, fieldname in mapping.items():
        if settings.meta.has_field(fieldname) and settings.get(fieldname) is not None:
            values[key] = settings.get(fieldname)

    web_form = _get_web_form_by_route(route)
    if web_form:
        _apply_web_form_design_overrides(values, web_form)

    for key in (
        "enabled",
        "use_company_branding",
        "show_hero_header",
        "show_privacy_notice",
        "sticky_actions",
        "hide_child_row_name",
    ):
        values[key] = cint(values[key])
    values.max_content_width = min(max(cint(values.max_content_width) or 1180, 760), 1600)

    company = values.get("branding_company") or values.default_company or frappe.defaults.get_global_default("company")
    branding = _get_company_branding(company) if values.use_company_branding else {}
    values.company = company
    values.company_name = branding.get("company_name") or company
    values.logo = branding.get("logo")
    values.primary_color = branding.get("primary_color") or "#176b87"
    values.secondary_color = branding.get("secondary_color") or "#0d4f67"
    values.accent_color = branding.get("accent_color") or "#2f855a"
    values.surface_color = branding.get("surface_color") or "#ffffff"
    return values


def _get_web_form_by_route(route):
    route = (route or "").strip().strip("/")
    if not route or not frappe.db.exists("DocType", "Web Form"):
        return None
    name = frappe.db.get_value("Web Form", {"route": route, "published": 1}, "name")
    return frappe.get_cached_doc("Web Form", name) if name else None


def _apply_web_form_design_overrides(values, web_form):
    mode = web_form.get("qorg_web_form_design_mode") or "Use Global Setting"
    if mode == "Standard Frappe Design":
        values.enabled = 0
        return
    if mode == "Enhanced Design":
        values.enabled = 1

    values.branding_company = web_form.get("qorg_web_form_branding_company")
    width = cint(web_form.get("qorg_web_form_max_content_width_override"))
    if width:
        values.max_content_width = width

    values.show_hero_header = _resolve_form_choice(
        web_form.get("qorg_web_form_hero_mode"),
        values.show_hero_header,
        "Show",
        "Hide",
    )
    values.show_privacy_notice = _resolve_form_choice(
        web_form.get("qorg_web_form_privacy_notice_mode"),
        values.show_privacy_notice,
        "Show",
        "Hide",
    )
    values.sticky_actions = _resolve_form_choice(
        web_form.get("qorg_web_form_sticky_actions_mode"),
        values.sticky_actions,
        "Enable",
        "Disable",
    )
    values.hide_child_row_name = _resolve_form_choice(
        web_form.get("qorg_web_form_child_name_mode"),
        values.hide_child_row_name,
        "Hide",
        "Show",
    )


def _resolve_form_choice(value, inherited, enabled_label, disabled_label):
    if value == enabled_label:
        return 1
    if value == disabled_label:
        return 0
    return inherited


def _get_company_branding(company):
    if not company or not frappe.db.exists("Company", company):
        return {}
    doc = frappe.get_cached_doc("Company", company)

    def first_value(*fieldnames):
        for fieldname in fieldnames:
            if doc.meta.has_field(fieldname) and doc.get(fieldname):
                return doc.get(fieldname)
        return None

    return {
        "company_name": doc.get("company_name") or doc.name,
        "logo": first_value("company_logo", "custom_company_logo", "custom_print_logo"),
        "primary_color": first_value("custom_print_primary_color", "custom_print_document_header_color"),
        "secondary_color": first_value("custom_print_document_header_color", "custom_print_primary_color"),
        "accent_color": first_value("custom_print_accent_color"),
        "surface_color": first_value("custom_print_light_color"),
    }


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
