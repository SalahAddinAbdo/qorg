from __future__ import annotations

import frappe

from qorg.qorg.enterprise_foundation.constants import CONFIGURATION_VERSION
from qorg.qorg.enterprise_foundation.features import (
    normalize_company_feature_rows,
    normalize_site_feature_rows,
)


def provision_enterprise_foundation():
    if not frappe.db.exists("DocType", "Feature Control Center"):
        return

    center = frappe.get_single("Feature Control Center")
    center.configuration_version = CONFIGURATION_VERSION
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
