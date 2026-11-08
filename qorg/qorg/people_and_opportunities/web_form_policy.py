from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint

MIN_CONTENT_WIDTH = 760
MAX_CONTENT_WIDTH = 1600
DESIGN_VERSION = "4.2.0"

DESIGN_DEFAULTS = {
    "qorg_web_form_design_mode": "Use Global Setting",
    "qorg_web_form_header_style_override": "Use Global Setting",
    "qorg_web_form_max_content_width_override": None,
    "qorg_web_form_privacy_notice_mode": "Use Global Setting",
    "qorg_web_form_sticky_actions_mode": "Use Global Setting",
    "qorg_web_form_child_name_mode": "Use Global Setting",
    "qorg_web_form_branding_company": None,
    "qorg_apply_managed_web_form_design": 1,
    "qorg_managed_css_version": DESIGN_VERSION,
    "qorg_managed_css_update_available": 0,
    "qorg_web_form_design_enabled": 1,
    "qorg_inherit_global_web_form_design": 1,
    "qorg_header_style": "Use Global Setting",
    "qorg_web_form_design_version": DESIGN_VERSION,
}

STANDARD_BOOLEAN_FIELDS = (
    "published", "is_standard", "login_required", "anonymous", "allow_multiple",
    "allow_edit", "allow_delete", "show_list", "allow_print",
    "apply_document_permissions", "key_required", "show_attachments", "show_sidebar",
    "allow_comments", "allow_incomplete", "show_title", "show_breadcrumbs",
)
STANDARD_TEXT_FIELDS = (
    "title", "route", "doc_type", "module", "introduction_text", "success_message",
    "submit_button_label", "list_title", "list_columns", "condition_json",
)


def _set_if_supported(doc, fieldname, value):
    if doc.meta.has_field(fieldname):
        doc.set(fieldname, value)


def apply_web_form_design_defaults(doc, overwrite=False):
    for fieldname, value in DESIGN_DEFAULTS.items():
        if not doc.meta.has_field(fieldname):
            continue
        if overwrite or doc.get(fieldname) in (None, ""):
            doc.set(fieldname, value)


def apply_managed_web_form_settings(doc, definition):
    for fieldname in STANDARD_TEXT_FIELDS + STANDARD_BOOLEAN_FIELDS:
        if fieldname not in definition:
            continue
        value = cint(definition[fieldname]) if fieldname in STANDARD_BOOLEAN_FIELDS else definition[fieldname]
        _set_if_supported(doc, fieldname, value)

    apply_web_form_design_defaults(doc)
    for fieldname, value in (definition.get("design") or {}).items():
        _set_if_supported(doc, fieldname, value)

    # Only managed definitions may explicitly clear or replace these fields.
    for fieldname in ("custom_css", "client_script"):
        if fieldname in definition:
            _set_if_supported(doc, fieldname, definition[fieldname])


def validate_web_form_policy(doc, method=None):
    apply_web_form_design_defaults(doc)
    fieldname = "qorg_web_form_max_content_width_override"
    if doc.meta.has_field(fieldname) and doc.get(fieldname) not in (None, "", 0, "0"):
        width = cint(doc.get(fieldname))
        if not MIN_CONTENT_WIDTH <= width <= MAX_CONTENT_WIDTH:
            frappe.throw(
                _("Maximum Content Width Override must be between {0} and {1} pixels.").format(
                    MIN_CONTENT_WIDTH, MAX_CONTENT_WIDTH
                )
            )
    if doc.meta.has_field("route") and doc.route:
        doc.route = str(doc.route).strip().strip("/")


def reconcile_web_form_policy():
    if not frappe.db.exists("DocType", "Web Form"):
        return {"updated": [], "preserved": []}
    updated, preserved = [], []
    for name in frappe.get_all("Web Form", pluck="name"):
        doc = frappe.get_doc("Web Form", name)
        before = {f: doc.get(f) for f in DESIGN_DEFAULTS if doc.meta.has_field(f)}
        apply_web_form_design_defaults(doc)
        after = {f: doc.get(f) for f in before}
        if before != after:
            doc.save(ignore_permissions=True)
            updated.append(name)
        else:
            preserved.append(name)
    frappe.clear_cache(doctype="Web Form")
    return {"updated": updated, "preserved": preserved, "design_version": DESIGN_VERSION}
