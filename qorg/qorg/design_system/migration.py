from __future__ import annotations

import hashlib

import frappe
from frappe import _

from qorg.qorg.design_system.provisioning import provision_design_system

SETTINGS_DOCTYPE = "Q Org Design System Settings"
PRESET_DOCTYPE = "Q Org Design Preset"
DEFAULT_PRESET = "Q Org Comfortable"

OBSOLETE_WEBSITE_FIELDS = (
    "qorg_enable_enhanced_web_form_design",
    "qorg_web_form_use_company_branding",
    "qorg_web_form_show_hero_header",
    "qorg_web_form_show_privacy_notice",
    "qorg_web_form_sticky_actions",
    "qorg_web_form_hide_child_row_name",
    "qorg_web_form_max_content_width",
    "qorg_web_form_header_style",
    "qorg_web_form_default_company",
)

OBSOLETE_WEB_FORM_FIELDS = (
    "qorg_managed_css_hash",
    "qorg_managed_css_version",
    "qorg_managed_css_update_available",
    "qorg_apply_managed_web_form_design",
)


def migrate_legacy_web_form_design() -> None:
    """Migrate the legacy Web Form design without leaving invalid links.

    The migration patch runs before ``after_migrate``. Therefore, the managed
    presets must be provisioned here before saving the Single settings record,
    whose ``active_preset`` Link may already contain its JSON default.
    """
    _provision_required_presets()
    _migrate_settings()
    _migrate_web_forms()
    _delete_obsolete_fields()
    frappe.clear_cache(doctype=SETTINGS_DOCTYPE)
    frappe.clear_cache(doctype="Web Form")


def _provision_required_presets() -> None:
    if not frappe.db.exists("DocType", PRESET_DOCTYPE):
        return

    provision_design_system()

    if not frappe.db.exists(PRESET_DOCTYPE, DEFAULT_PRESET):
        frappe.throw(
            _("Could not provision the required design preset: {0}").format(
                DEFAULT_PRESET
            )
        )


def _migrate_settings() -> None:
    if not frappe.db.exists("DocType", SETTINGS_DOCTYPE):
        return

    settings = frappe.get_single(SETTINGS_DOCTYPE)
    changed = False

    # A Single DocType may expose its JSON Link default before the linked record
    # exists. Repair that state defensively, even on partially failed migrations.
    active_preset = settings.get("active_preset")
    if active_preset and not frappe.db.exists(PRESET_DOCTYPE, active_preset):
        settings.active_preset = DEFAULT_PRESET
        changed = True
    elif not active_preset:
        settings.active_preset = DEFAULT_PRESET
        changed = True

    if frappe.db.exists("DocType", "Website Settings"):
        website_settings = frappe.get_single("Website Settings")
        mapping = {
            "qorg_enable_enhanced_web_form_design": "apply_to_qorg_web_components",
            "qorg_web_form_sticky_actions": "web_form_sticky_actions",
            "qorg_web_form_hide_child_row_name": (
                "web_form_hide_technical_child_row_name"
            ),
        }

        for source, target in mapping.items():
            if not website_settings.meta.has_field(source):
                continue
            if not settings.meta.has_field(target):
                continue

            value = website_settings.get(source)
            if value in (None, ""):
                continue

            if settings.get(target) != value:
                settings.set(target, value)
                changed = True

        # Legacy Int fields can contain 0 when they were never configured.
        # Never copy that sentinel into the new validated width setting.
        if settings.meta.has_field("web_form_max_content_width"):
            legacy_width = (
                website_settings.get("qorg_web_form_max_content_width")
                if website_settings.meta.has_field("qorg_web_form_max_content_width")
                else None
            )
            try:
                legacy_width = int(legacy_width or 0)
            except (TypeError, ValueError):
                legacy_width = 0

            target_width = settings.get("web_form_max_content_width")
            try:
                target_width = int(target_width or 0)
            except (TypeError, ValueError):
                target_width = 0

            if 760 <= legacy_width <= 1600:
                if target_width != legacy_width:
                    settings.web_form_max_content_width = legacy_width
                    changed = True
            elif not 760 <= target_width <= 1600:
                settings.web_form_max_content_width = 1180
                changed = True

    # Repair an invalid zero or out-of-range value left by a previous failed
    # migration, even when Website Settings or the legacy field is absent.
    if settings.meta.has_field("web_form_max_content_width"):
        try:
            current_width = int(settings.get("web_form_max_content_width") or 0)
        except (TypeError, ValueError):
            current_width = 0
        if not 760 <= current_width <= 1600:
            settings.web_form_max_content_width = 1180
            changed = True

    if changed:
        settings.flags.ignore_permissions = True
        settings.save()


def _migrate_web_forms() -> None:
    if not frappe.db.exists("DocType", "Web Form"):
        return

    for name in frappe.get_all("Web Form", pluck="name"):
        doc = frappe.get_doc("Web Form", name)
        css = doc.custom_css or ""
        stored_hash = (
            doc.get("qorg_managed_css_hash")
            if doc.meta.has_field("qorg_managed_css_hash")
            else None
        )
        current_hash = hashlib.sha256(css.encode("utf-8")).hexdigest() if css else ""

        # Remove only CSS that is proven to be the untouched managed payload.
        # User-modified and unknown CSS remains exactly as it is.
        if css and stored_hash and current_hash == stored_hash:
            doc.custom_css = ""
            doc.flags.ignore_permissions = True
            doc.save()


def _delete_obsolete_fields() -> None:
    for doctype, fieldnames in (
        ("Website Settings", OBSOLETE_WEBSITE_FIELDS),
        ("Web Form", OBSOLETE_WEB_FORM_FIELDS),
    ):
        for fieldname in fieldnames:
            name = f"{doctype}-{fieldname}"
            if frappe.db.exists("Custom Field", name):
                frappe.delete_doc(
                    "Custom Field",
                    name,
                    ignore_permissions=True,
                    force=True,
                )
