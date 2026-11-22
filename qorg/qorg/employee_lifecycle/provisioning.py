from __future__ import annotations

import frappe
from qorg.qorg.enterprise_foundation.idempotent_provisioning import create_custom_fields_if_changed

FIELDS = {
    "Employee": [
        {"fieldname":"qorg_lifecycle_section","label":"QOrg Employee Lifecycle","fieldtype":"Section Break","insert_after":"qorg_recruitment_source_cb","collapsible":1},
        {"fieldname":"qorg_employment_contract","label":"Current Employment Contract","fieldtype":"Link","options":"Contract","insert_after":"qorg_lifecycle_section","read_only":1},
        {"fieldname":"qorg_service_activation_status","label":"Service Activation Status","fieldtype":"Select","options":"Not Evaluated\nBlocked\nPartially Ready\nReady\nActivated","default":"Not Evaluated","insert_after":"qorg_employment_contract","read_only":1,"in_standard_filter":1},
        {"fieldname":"qorg_lifecycle_column","fieldtype":"Column Break","insert_after":"qorg_service_activation_status"},
        {"fieldname":"qorg_employment_effective_date","label":"Employment Effective Date","fieldtype":"Date","insert_after":"qorg_lifecycle_column","read_only":1},
        {"fieldname":"qorg_payroll_effective_date","label":"Payroll Effective Date","fieldtype":"Date","insert_after":"qorg_employment_effective_date","read_only":1},
        {"fieldname":"qorg_attendance_effective_date","label":"Attendance Effective Date","fieldtype":"Date","insert_after":"qorg_payroll_effective_date","read_only":1},
        {"fieldname":"qorg_leave_effective_date","label":"Leave Effective Date","fieldtype":"Date","insert_after":"qorg_attendance_effective_date","read_only":1},
    ],
    "Employee Onboarding": [
        {"fieldname":"qorg_lifecycle_section","label":"QOrg Lifecycle Source","fieldtype":"Section Break","insert_after":"qorg_onboarding_context_cb","collapsible":1},
        {"fieldname":"qorg_work_commencement_notice","label":"Work Commencement Notice","fieldtype":"Link","options":"Work Commencement Notice","insert_after":"qorg_lifecycle_section","read_only":1},
        {"fieldname":"qorg_employment_contract","label":"Employment Contract","fieldtype":"Link","options":"Contract","insert_after":"qorg_work_commencement_notice","read_only":1},
    ],
}


def reconcile_employee_contract_type():
    """Align Employment Contract with HR ownership of salary and open/fixed terms."""
    if not frappe.db.exists("QOrg Contract Type", "Employment Contract"):
        return
    doc = frappe.get_doc("QOrg Contract Type", "Employment Contract")
    changed = False
    values = {
        "requires_value": 0,
        "allows_zero_value": 1,
        "allows_open_ended_period": 1,
        "requires_employee": 1,
        "requires_payroll_activation": 1,
        "requires_procurement_source": 0,
        "party_model": "Standard Party",
        "default_party_type": "Employee",
    }
    for fieldname, value in values.items():
        if doc.get(fieldname) != value:
            doc.set(fieldname, value)
            changed = True
    if not any(row.party_mode == "Standard" and row.party_doctype == "Employee" for row in doc.allowed_parties):
        doc.append("allowed_parties", {"party_mode":"Standard","party_doctype":"Employee","is_default":1,"is_active":1})
        changed = True
    if changed:
        doc.save(ignore_permissions=True)


def provision_employee_lifecycle():
    definitions = {dt: rows for dt, rows in FIELDS.items() if frappe.db.exists("DocType", dt)}
    result = create_custom_fields_if_changed(definitions, update=True) if definitions else {"changed": [], "unchanged": []}
    reconcile_employee_contract_type()
    return result
