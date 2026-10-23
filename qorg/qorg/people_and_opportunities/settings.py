from __future__ import annotations

import frappe
from frappe import _dict

from qorg.qorg.enterprise_foundation.features import (
    get_feature_settings,
    is_feature_enabled,
)

DEFAULTS = {
    "default_cv_print_format": "External Person CV",
    "profile_minimum_completion": 60,
    "allow_profile_web_update": 1,
    "default_data_retention_days": 730,
    "match_by_email": 1,
    "match_by_mobile": 1,
    "match_by_official_id": 1,
    "closing_reminder_days": 3,
    "require_opportunity_approval": 1,
    "allow_public_opportunity_listing": 0,
    "allow_guest_opportunity_view": 1,
    "privacy_notice": "",
    "portal_terms": "",
}


def settings(company: str | None = None) -> _dict:
    """Resolve package settings from Enterprise Foundation configuration.

    Site and company feature configuration are already managed by Feature Control
    Center and Company Feature Settings. Reusing them avoids a parallel Settings
    DocType and follows the application's single-source-of-truth policy.
    """
    resolved = dict(DEFAULTS)
    for feature_key in (
        "external_people",
        "public_opportunities",
        "extended_recruitment",
        "volunteer_management",
    ):
        feature = get_feature_settings(company, feature_key)
        configuration = feature.get("configuration") or {}
        for key in DEFAULTS:
            if key in configuration:
                resolved[key] = configuration[key]
    return _dict(resolved)


def require_feature(feature_key: str, company: str | None = None) -> None:
    if frappe.session.user == "Administrator":
        return
    if not is_feature_enabled(company, feature_key):
        frappe.throw(f"Feature {feature_key} is disabled.", frappe.PermissionError)
