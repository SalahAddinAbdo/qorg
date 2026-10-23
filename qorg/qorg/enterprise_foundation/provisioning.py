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


def provision_enterprise_foundation():
    if not frappe.db.exists("DocType", "Feature Control Center"):
        return

    center = frappe.get_single("Feature Control Center")
    center.configuration_version = CONFIGURATION_VERSION

    # Cleanup must run before save because Frappe validates every Select value
    # in child rows during Document._validate().
    _cleanup_legacy_model_rows(center)
    _cleanup_obsolete_interface_rows(center)
    normalize_site_feature_rows(center)

    center.flags.ignore_permissions = True
    center.save()

    if frappe.db.exists("DocType", "Company Feature Settings"):
        for name in frappe.get_all("Company Feature Settings", pluck="name"):
            settings = frappe.get_doc("Company Feature Settings", name)
            settings.configuration_version = CONFIGURATION_VERSION
            normalize_company_feature_rows(settings)
            settings.flags.ignore_permissions = True
            settings.save()

    frappe.clear_cache()
