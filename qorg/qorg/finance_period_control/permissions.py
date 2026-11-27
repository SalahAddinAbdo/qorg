import frappe
from frappe.permissions import add_permission, update_permission_property

REPORTS = (
    "Commitment Lifecycle Summary",
    "Commitment Reconciliation Exceptions",
    "Commitment Distribution Exceptions",
    "Cross Period Reconciliation",
)


def ensure_finance_permissions():
    role_permissions = {
        "Accounts User":{"read":1,"report":1,"export":1},
        "Accounts Manager":{"read":1,"write":1,"create":1,"report":1,"export":1},
        "System Manager":{"read":1,"write":1,"create":1,"delete":1,"report":1,"export":1,"share":1},
    }
    for role, properties in role_permissions.items():
        if not frappe.db.exists("Custom DocPerm", {"parent":"Commitment Ledger","role":role,"permlevel":0}):
            add_permission("Commitment Ledger", role, 0)
        for property_name, value in properties.items():
            update_permission_property("Commitment Ledger", role, 0, property_name, value)
    for report in REPORTS:
        if frappe.db.exists("Report", report):
            frappe.db.set_value("Report", report, "ref_doctype", "Commitment Ledger", update_modified=False)
