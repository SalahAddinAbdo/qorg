from __future__ import annotations

from functools import lru_cache

import frappe
from frappe.utils import getdate, nowdate

from qorg.qorg.enterprise_foundation.constants import CONFIGURATION_VERSION, FEATURES

FEATURE_MAP = {key: {"label": label, "minimum_mode": mode} for key, label, mode in FEATURES}


def normalize_feature_rows(doc) -> None:
    existing = {row.feature_key: row for row in (doc.features or []) if row.feature_key}
    ordered = []
    for key, label, _minimum_mode in FEATURES:
        row = existing.get(key)
        if not row:
            row = doc.append("features", {})
        row.feature_key = key
        row.feature_label = label
        row.managed_version = CONFIGURATION_VERSION
        ordered.append(row)
    doc.set("features", ordered)


def get_company_settings(company: str | None):
    if not company or not frappe.db.exists("DocType", "Company Feature Settings"):
        return None
    name = frappe.db.get_value("Company Feature Settings", {"company": company, "enabled": 1}, "name")
    return frappe.get_cached_doc("Company Feature Settings", name) if name else None


def get_operating_mode(company: str | None) -> str:
    settings = get_company_settings(company)
    return settings.operating_mode if settings else "Standard Only"


def is_feature_enabled(company: str | None, feature_key: str) -> bool:
    if feature_key not in FEATURE_MAP:
        return False
    settings = get_company_settings(company)
    if not settings:
        return False
    today = getdate(nowdate())
    for row in settings.features or []:
        if row.feature_key != feature_key or not row.enabled:
            continue
        if row.effective_from and getdate(row.effective_from) > today:
            return False
        if row.effective_to and getdate(row.effective_to) < today:
            return False
        return True
    return False


def get_feature_settings(company: str | None, feature_key: str) -> dict:
    settings = get_company_settings(company)
    if not settings:
        return {"enabled": False, "operating_mode": "Standard Only", "configuration": {}}
    for row in settings.features or []:
        if row.feature_key == feature_key:
            configuration = {}
            if row.configuration:
                try:
                    configuration = frappe.parse_json(row.configuration) or {}
                except Exception:
                    configuration = {}
            return {
                "enabled": is_feature_enabled(company, feature_key),
                "operating_mode": settings.operating_mode if row.operating_mode == "Inherit" else row.operating_mode,
                "configuration": configuration,
            }
    return {"enabled": False, "operating_mode": settings.operating_mode, "configuration": {}}
