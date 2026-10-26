from __future__ import annotations

import frappe

from qorg.qorg.enterprise_foundation.constants import CONFIGURATION_VERSION
from qorg.qorg.enterprise_foundation.features import (
    normalize_company_feature_rows,
    normalize_site_feature_rows,
)

# These are the interface component types that remain supported by the current
# Interface Control Entry schema. Print Format was intentionally removed.
SUPPORTED_INTERFACE_TYPES = {
    "Report",
    "Page",
    "Workspace",
    "Dashboard",
    "Number Card",
    "Web Form",
    "Web Page",
}

# Compatibility mapping for rows created by the earlier experimental action
# policy. The current design has only Standard and View Only.
LEGACY_ACTION_POLICY_MAP = {
    "Disable Write Actions": "View Only",
}


def _cleanup_legacy_model_rows(center) -> None:
    if not center.meta.has_field("models"):
        return

    for row in center.models or []:
        if row.current_action_policy in LEGACY_ACTION_POLICY_MAP:
            row.current_action_policy = LEGACY_ACTION_POLICY_MAP[row.current_action_policy]
        if row.requested_action_policy in LEGACY_ACTION_POLICY_MAP:
            row.requested_action_policy = LEGACY_ACTION_POLICY_MAP[row.requested_action_policy]


def _cleanup_obsolete_interface_rows(center) -> None:
    if not center.meta.has_field("interface_components"):
        return

    valid_rows = []
    for row in center.interface_components or []:
        if row.component_type in SUPPORTED_INTERFACE_TYPES:
            valid_rows.append(row)

    # Replacing the child collection before save is migration-safe and removes
    # old Print Format rows before Select validation runs.
    center.set("interface_components", valid_rows)


def _cleanup_missing_doctype_links(document) -> list[dict]:
    """Remove child rows that reference DocTypes no longer installed.

    Frappe removes orphaned standard DocTypes during migrate before after_migrate
    hooks run. Managed inventory rows can therefore retain invalid Link values
    and block saving their parent settings document. Only child rows containing
    a missing Link whose options are DocType are removed.
    """
    removed_rows: list[dict] = []

    for table_field in document.meta.get_table_fields():
        valid_rows = []

        for row in document.get(table_field.fieldname) or []:
            missing_links = []
            child_meta = frappe.get_meta(row.doctype)

            for field in child_meta.fields:
                if field.fieldtype != "Link" or field.options != "DocType":
                    continue

                linked_doctype = row.get(field.fieldname)
                if linked_doctype and not frappe.db.exists("DocType", linked_doctype):
                    missing_links.append(
                        {
                            "fieldname": field.fieldname,
                            "doctype": linked_doctype,
                        }
                    )

            if missing_links:
                removed_rows.append(
                    {
                        "parent_doctype": document.doctype,
                        "parent_name": document.name,
                        "table_field": table_field.fieldname,
                        "child_doctype": row.doctype,
                        "child_name": row.name,
                        "idx": row.idx,
                        "missing_links": missing_links,
                    }
                )
                continue

            valid_rows.append(row)

        document.set(table_field.fieldname, valid_rows)

    return removed_rows


def _log_removed_missing_doctype_links(removed_rows: list[dict]) -> None:
    if not removed_rows:
        return

    frappe.logger("qorg").warning(
        {
            "event": "removed_missing_doctype_inventory_rows",
            "rows": removed_rows,
        }
    )


def provision_enterprise_foundation():
    if not frappe.db.exists("DocType", "Feature Control Center"):
        return

    center = frappe.get_single("Feature Control Center")
    center.configuration_version = CONFIGURATION_VERSION

    # Cleanup must run before save because Frappe validates Link and Select
    # values in every retained child row during Document._validate().
    _cleanup_legacy_model_rows(center)
    _cleanup_obsolete_interface_rows(center)
    normalize_site_feature_rows(center)
    removed_rows = _cleanup_missing_doctype_links(center)

    center.flags.ignore_permissions = True
    center.save()
    _log_removed_missing_doctype_links(removed_rows)

    if frappe.db.exists("DocType", "Company Feature Settings"):
        for name in frappe.get_all("Company Feature Settings", pluck="name"):
            settings = frappe.get_doc("Company Feature Settings", name)
            settings.configuration_version = CONFIGURATION_VERSION
            normalize_company_feature_rows(settings)
            removed_rows = _cleanup_missing_doctype_links(settings)
            settings.flags.ignore_permissions = True
            settings.save()
            _log_removed_missing_doctype_links(removed_rows)

    frappe.clear_cache()
