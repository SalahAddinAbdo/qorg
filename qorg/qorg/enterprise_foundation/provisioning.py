from __future__ import annotations

import frappe

from qorg.qorg.enterprise_foundation.constants import CONFIGURATION_VERSION, FEATURES


def provision_enterprise_foundation():
    if not frappe.db.exists("DocType", "Feature Control Center"):
        return
    doc=frappe.get_single("Feature Control Center")
    doc.configuration_version=CONFIGURATION_VERSION
    existing={row.feature_key:row for row in (doc.site_features or []) if row.feature_key}
    rows=[]
    for key,label,_mode in FEATURES:
        row=existing.get(key) or doc.append("site_features", {})
        row.feature_key=key; row.feature_label=label; row.managed_version=CONFIGURATION_VERSION
        rows.append(row)
    doc.set("site_features", rows)
    doc.flags.ignore_permissions=True
    doc.save()
    frappe.clear_cache()
