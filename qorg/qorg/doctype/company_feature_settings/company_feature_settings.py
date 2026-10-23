from __future__ import annotations

import frappe
from frappe.model.document import Document
from frappe.utils import flt

from qorg.qorg.enterprise_foundation.constants import CONFIGURATION_VERSION
from qorg.qorg.enterprise_foundation.features import normalize_company_feature_rows


class CompanyFeatureSettings(Document):
    def validate(self):
        if not frappe.db.exists("Company", self.company):
            frappe.throw("Select a valid Company.")

        duplicate = frappe.db.get_value(
            "Company Feature Settings",
            {"company": self.company, "name": ("!=", self.name or "")},
            "name",
        )
        if duplicate:
            frappe.throw(f"Feature settings already exist for Company {self.company}.")

        self.minimum_gps_accuracy = max(flt(self.minimum_gps_accuracy), 0)
        if self.mobile_attendance_mode in ("Geofenced Attendance", "Field Attendance"):
            self.require_geolocation = 1
        if self.mobile_attendance_mode == "Disabled":
            self.require_geolocation = 0
            self.allow_off_site_checkin = 0

        self.configuration_version = CONFIGURATION_VERSION
        normalize_company_feature_rows(self)

    def on_update(self):
        frappe.clear_cache()
