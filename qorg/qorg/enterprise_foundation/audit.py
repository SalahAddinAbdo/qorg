from __future__ import annotations

import frappe
from frappe.utils import now_datetime

from qorg.qorg.enterprise_foundation.constants import CRITICAL_DOCTYPES


def audit_control_center(doc) -> list[dict]:
    findings = []
    for row in doc.models or []:
        if row.document_type in CRITICAL_DOCTYPES and row.requested_policy != "Enabled":
            findings.append({"severity":"Blocked","category":"Critical Model","reference_doctype":"DocType","reference_name":row.document_type,"message":f"{row.document_type} is critical and cannot be disabled.","suggested_action":"Keep the model enabled.","detected_on":now_datetime()})
        if row.requested_policy in ("Restricted", "Read Only", "Feature Disabled", "Deprecated") and row.record_count:
            findings.append({"severity":"Warning","category":"Existing Data","reference_doctype":"DocType","reference_name":row.document_type,"message":f"{row.document_type} contains {row.record_count} records.","suggested_action":"Preserve historical read access and review dependencies before applying.","detected_on":now_datetime()})
        if row.incoming_links and row.requested_policy in ("Feature Disabled", "Deprecated"):
            findings.append({"severity":"Warning","category":"Dependency","reference_doctype":"DocType","reference_name":row.document_type,"message":f"{row.document_type} has {row.incoming_links} incoming Link fields.","suggested_action":"Review linked workflows, reports, and forms.","detected_on":now_datetime()})
    return findings


def audit_company_settings(doc) -> list[str]:
    issues=[]
    if doc.mobile_attendance_mode in ("Geofenced Attendance", "Field Attendance") and not doc.require_geolocation:
        issues.append("Geolocation is required for the selected mobile attendance mode.")
    if doc.mobile_attendance_mode == "Disabled" and any((doc.require_geolocation, doc.allow_off_site_checkin)):
        issues.append("Mobile attendance controls are active while mobile attendance is disabled.")
    return issues
