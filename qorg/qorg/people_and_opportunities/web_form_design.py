from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint

DEFAULT_MAX_CONTENT_WIDTH = 1180
MIN_CONTENT_WIDTH = 760
MAX_CONTENT_WIDTH = 1600


def validate_website_settings(doc, method=None) -> None:
    """Compatibility validator for Website Settings.

    Global visual configuration now lives in QOrg Design System Settings, but
    portal_settings and existing hooks still import this stable function name.
    Only validate the legacy width when the field exists and contains a positive
    configured value. Zero means that the legacy field was never configured.
    """
    fieldname = "qorg_web_form_max_content_width"
    if not doc.meta.has_field(fieldname):
        return

    raw_value = doc.get(fieldname)
    if raw_value in (None, "", 0, "0"):
        return

    width = cint(raw_value)
    if width < MIN_CONTENT_WIDTH or width > MAX_CONTENT_WIDTH:
        frappe.throw(
            _("Maximum Content Width must be between {0} and {1} pixels.").format(
                MIN_CONTENT_WIDTH,
                MAX_CONTENT_WIDTH,
            )
        )


def validate_web_form_design_settings(doc, method=None) -> None:
    """Backward-compatible alias retained for internal callers."""
    validate_website_settings(doc, method)


def apply_managed_design(doc, method=None, force=False, save=False):
    """Do not write generated CSS into Web Form.custom_css.

    Design is now applied by the central website bundle. The function remains
    available because older provisioning code and integrations may still import
    it during an upgrade. Existing user CSS is deliberately left untouched.
    """
    return "preserved"


def reconcile_all_web_form_designs(doc=None, method=None, force=False):
    """Return a compatibility reconciliation result without rewriting CSS."""
    preserved = []
    if frappe.db.exists("DocType", "Web Form"):
        preserved = frappe.get_all("Web Form", pluck="name")

    return {
        "updated": [],
        "preserved": preserved,
        "design_source": "QOrg Design System Settings",
    }
