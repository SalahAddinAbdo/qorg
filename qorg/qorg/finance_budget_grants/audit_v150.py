from __future__ import annotations
import frappe

REQUIRED_DOCTYPES = [
    "Funding Agreement", "Funding Budget Rule", "Project Funding Source",
    "Budget Transfer Item", "Budget Transfer Audit", "Budget Transfer Audit Row",
    "Project Change Request", "Budget Line", "Project"
]
REQUIRED_PCR_FIELDS = [
    "funding_agreement", "budget_transfer_required", "budget_transfer_rows",
    "budget_transfer_amount", "donor_approval_required", "donor_approval_status",
    "budget_transfer_applied_on", "budget_transfer_applied_by", "budget_transfer_audit"
]

def audit_v150():
    missing_doctypes = [d for d in REQUIRED_DOCTYPES if not frappe.db.exists("DocType", d)]
    meta = frappe.get_meta("Project Change Request")
    missing_fields = [f for f in REQUIRED_PCR_FIELDS if not meta.has_field(f)]
    project_meta = frappe.get_meta("Project")
    funding_table_ok = bool(project_meta.get_field("custom_funding_sources") and project_meta.get_field("custom_funding_sources").options == "Project Funding Source")
    hooks = frappe.get_hooks("doc_events") or {}
    result = {
        "version":"1.5.0", "missing_doctypes":missing_doctypes,
        "missing_project_change_request_fields":missing_fields,
        "project_funding_table_ok":funding_table_ok,
        "passed":not missing_doctypes and not missing_fields and funding_table_ok
    }
    return result
