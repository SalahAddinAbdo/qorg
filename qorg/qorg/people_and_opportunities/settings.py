from __future__ import annotations
import frappe
from qorg.qorg.enterprise_foundation.features import is_feature_enabled

def settings():
    return frappe.get_cached_doc("People and Opportunities Settings")

def require_feature(feature_key: str, company: str | None = None) -> None:
    if frappe.session.user == "Administrator":
        return
    if not is_feature_enabled(company, feature_key):
        frappe.throw(f"Feature {feature_key} is disabled.", frappe.PermissionError)
