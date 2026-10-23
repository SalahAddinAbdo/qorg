from __future__ import annotations

import json

import frappe
from frappe.utils import getdate, nowdate

from qorg.qorg.enterprise_foundation.constants import CONFIGURATION_VERSION, FEATURES

FEATURE_MAP = {
    key: {"label": label, "minimum_mode": mode}
    for key, label, mode in FEATURES
}
VALID_STATES = {"Inherit", "Enabled", "Disabled"}
VALID_MODES = {"Inherit", "Standard Only", "Extensions", "Full Portal / Extended Cycle"}


def _row_state(row, *, site_level: bool) -> str:
    state = (getattr(row, "feature_state", None) or "").strip()
    if state not in VALID_STATES:
        state = "Enabled" if getattr(row, "enabled", 0) else ("Disabled" if site_level else "Inherit")
    if site_level and state == "Inherit":
        return "Disabled"
    return state


def _row_mode(row, *, fallback: str) -> str:
    mode = (getattr(row, "operating_mode", None) or "Inherit").strip()
    if mode not in VALID_MODES or mode == "Inherit":
        return fallback
    return mode


def _sync_legacy_enabled(row, state: str) -> None:
    # Keep the old database column synchronized for upgrade compatibility only.
    row.enabled = 1 if state == "Enabled" else 0


def _normalize_rows(doc, *, site_level: bool) -> None:
    existing = {row.feature_key: row for row in (doc.get("features") or doc.get("site_features") or []) if row.feature_key}
    parentfield = "site_features" if site_level else "features"
    normalized = []

    for key, label, _minimum_mode in FEATURES:
        row = existing.get(key)
        if not row:
            row = doc.append(parentfield, {})
        state = _row_state(row, site_level=site_level)
        row.feature_key = key
        row.feature_label = label
        row.feature_state = state
        row.operating_mode = row.operating_mode or "Inherit"
        row.managed_version = CONFIGURATION_VERSION
        _sync_legacy_enabled(row, state)
        normalized.append(row)

    doc.set(parentfield, normalized)


def normalize_company_feature_rows(doc) -> None:
    _normalize_rows(doc, site_level=False)


def normalize_site_feature_rows(doc) -> None:
    _normalize_rows(doc, site_level=True)


def get_company_settings(company: str | None):
    if not company or not frappe.db.exists("DocType", "Company Feature Settings"):
        return None
    name = frappe.db.get_value(
        "Company Feature Settings",
        {"company": company, "enabled": 1},
        "name",
    )
    return frappe.get_cached_doc("Company Feature Settings", name) if name else None


def get_site_feature_row(feature_key: str):
    if not frappe.db.exists("DocType", "Feature Control Center"):
        return None
    center = frappe.get_cached_doc("Feature Control Center")
    for row in center.site_features or []:
        if row.feature_key == feature_key:
            return row
    return None


def get_company_feature_row(settings, feature_key: str):
    if not settings:
        return None
    for row in settings.features or []:
        if row.feature_key == feature_key:
            return row
    return None


def _is_effective_now(row) -> bool:
    today = getdate(nowdate())
    if row and row.effective_from and getdate(row.effective_from) > today:
        return False
    if row and row.effective_to and getdate(row.effective_to) < today:
        return False
    return True


def _configuration(row) -> dict:
    if not row or not row.configuration:
        return {}
    try:
        value = frappe.parse_json(row.configuration)
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def resolve_feature_state(company: str | None, feature_key: str) -> dict:
    if feature_key not in FEATURE_MAP:
        return {
            "feature_key": feature_key,
            "enabled": False,
            "operating_mode": "Standard Only",
            "source": "Unknown Feature",
            "configuration": {},
        }

    site_row = get_site_feature_row(feature_key)
    site_state = _row_state(site_row, site_level=True) if site_row else "Disabled"
    site_enabled = site_state == "Enabled" and _is_effective_now(site_row)
    site_mode = _row_mode(site_row, fallback="Standard Only") if site_enabled else "Standard Only"

    settings = get_company_settings(company)
    company_row = get_company_feature_row(settings, feature_key)
    company_state = _row_state(company_row, site_level=False) if company_row else "Inherit"

    if settings and company_state == "Enabled":
        enabled = _is_effective_now(company_row)
        mode = _row_mode(company_row, fallback=settings.operating_mode or "Standard Only") if enabled else "Standard Only"
        source = "Company Override"
        configuration = _configuration(company_row)
    elif settings and company_state == "Disabled":
        enabled = False
        mode = "Standard Only"
        source = "Company Override"
        configuration = _configuration(company_row)
    else:
        enabled = site_enabled
        company_mode = settings.operating_mode if settings else "Standard Only"
        mode = _row_mode(company_row, fallback=site_mode or company_mode) if enabled else "Standard Only"
        if mode == "Standard Only" and enabled:
            # Enabled with Standard Only means the extension is installed but inactive.
            enabled = False
        source = "Site Default" if site_row else "Safe Default"
        configuration = {**_configuration(site_row), **_configuration(company_row)}

    return {
        "feature_key": feature_key,
        "enabled": bool(enabled),
        "operating_mode": mode,
        "source": source,
        "site_state": site_state,
        "company_state": company_state,
        "configuration": configuration,
    }


def get_operating_mode(company: str | None) -> str:
    settings = get_company_settings(company)
    return settings.operating_mode if settings else "Standard Only"


def is_feature_enabled(company: str | None, feature_key: str) -> bool:
    return bool(resolve_feature_state(company, feature_key)["enabled"])


def get_feature_settings(company: str | None, feature_key: str) -> dict:
    return resolve_feature_state(company, feature_key)
