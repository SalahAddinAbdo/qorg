import frappe

DOCTYPES = (
    "Stock Handover",
    "Stock Handover Item",
    "Asset Custody",
    "Custody Accessory",
    "Asset Incident",
    "Incident Action",
    "Physical Verification",
    "Verification Item",
)

REPORTS = (
    "Procurement Receipt Trace",
    "Purchase Receipt Status",
    "Rejected Replacement",
    "Stock Funding Status",
    "Pending Material Issue",
    "Unacknowledged Issue",
    "Handover Discrepancy",
    "Activity Material Usage",
    "Donor Asset Register",
    "Asset Custody Status",
    "Overdue Custody",
    "Asset Maintenance Status",
    "Damaged Missing Assets",
    "Physical Inventory Variance",
    "Movement Audit",
)

# Authoritative notification records after communication cleanup.
NOTIFICATIONS = (
    "Inventory - Receipt Inspection Required",
    "Inventory - Handover Pending",
    "Inventory - Handover Discrepancy",
    "Inventory - Incident Decision Pending",
    "Inventory - Verification Approval Pending",
)

TEMPLATES = (
    "Receipt Inspection Required",
    "Stock Handover Notice",
    "Handover Discrepancy Notice",
    "Incident Decision Pending",
    "Verification Approval Pending",
    "Asset Custody Notice",
    "Asset Incident Notice",
    "Custody Return Reminder",
    "Inspection Due Reminder",
    "Verification Approval Notice",
)


def audit_runtime_configuration():
    result = {
        "missing_doctypes": [name for name in DOCTYPES if not frappe.db.exists("DocType", name)],
        "missing_reports": [name for name in REPORTS if not frappe.db.exists("Report", name)],
        "missing_notifications": [
            name for name in NOTIFICATIONS if not frappe.db.exists("Notification", name)
        ],
        "missing_templates": [
            name for name in TEMPLATES if not frappe.db.exists("Email Template", name)
        ],
        "missing_workspace": (
            [] if frappe.db.exists("Workspace", "Inventory and Assets") else ["Inventory and Assets"]
        ),
    }
    result["passed"] = not any(result.values())
    return result
