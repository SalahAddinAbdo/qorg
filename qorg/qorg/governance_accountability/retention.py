from __future__ import annotations

import frappe
from frappe.utils import add_days, nowdate, now_datetime

CLOSED_STATUSES = ("Closed", "Withdrawn", "Duplicate", "Out of Scope", "Referred Externally")


def run_daily_retention_jobs():
    if not frappe.db.exists("DocType", "Accountability Case"):
        return {"ok": True, "skipped": True}
    settings = frappe.get_single("Accountability Settings")
    tracking_cutoff = add_days(nowdate(), -int(settings.disable_tracking_after_closure_days or 0))
    anonymize_cutoff = add_days(nowdate(), -int(settings.anonymize_contact_after_days or 0))
    tracking_disabled = 0
    anonymized = 0
    if int(settings.disable_tracking_after_closure_days or 0) > 0:
        names = frappe.get_all("Accountability Case", filters={"status": ["in", CLOSED_STATUSES], "closed_on": ["<=", tracking_cutoff], "external_tracking_enabled": 1}, pluck="name")
        for name in names:
            frappe.db.set_value("Accountability Case", name, {"external_tracking_enabled": 0, "external_tracking_key_hash": None}, update_modified=False)
        tracking_disabled = len(names)
    if int(settings.anonymize_contact_after_days or 0) > 0:
        names = frappe.get_all("Accountability Case", filters={"status": ["in", CLOSED_STATUSES], "closed_on": ["<=", anonymize_cutoff], "anonymous": 0}, pluck="name")
        for name in names:
            frappe.db.set_value("Accountability Case", name, {
                "reporter_name": "Anonymized after retention period", "email": None, "mobile_no": None,
                "employee": None, "external_person": None, "supplier": None, "contact": None,
                "consent_to_contact": 0,
            }, update_modified=False)
        anonymized = len(names)
    return {"ok": True, "tracking_disabled": tracking_disabled, "contacts_anonymized": anonymized, "run_on": now_datetime()}
