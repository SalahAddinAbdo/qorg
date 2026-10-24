import frappe
from frappe import _


def _exists(doctype, filters):
    return frappe.db.exists("DocType", doctype) and frappe.db.exists(doctype, filters)


def prevent_operational_delete(doc, method=None):
    rules = {
        "Participation Application": [
            ("Participation Assessment", {"application": doc.name}),
            ("Participation Engagement", {"application": doc.name, "docstatus": ["<", 2]}),
        ],
        "Participation Assessment": [
            ("Participation Assessment", {"previous_assessment": doc.name, "name": ["!=", doc.name]}),
        ],
        "Participation Engagement": [
            ("Participation Service Log", {"engagement": doc.name}),
            ("Participation Evaluation", {"engagement": doc.name}),
            ("Participation Certificate", {"engagement": doc.name}),
        ],
        "Participation Service Log": [],
        "Participation Evaluation": [],
        "Participation Certificate": [],
    }
    for target, filters in rules.get(doc.doctype, []):
        if _exists(target, filters):
            frappe.throw(_("Cannot delete {0} because linked {1} records exist. Cancel or close the operational record instead.").format(doc.doctype, target))
    protected_statuses = {
        "Participation Application": {"Selected", "Reserve / Waitlisted"},
        "Participation Assessment": {"Completed"},
        "Participation Engagement": {"Active", "Suspended", "Completed", "Terminated", "Withdrawn"},
        "Participation Service Log": {"Submitted", "Verified"},
        "Participation Evaluation": {"Completed"},
        "Participation Certificate": {"Issued", "Revoked"},
    }
    status = doc.get("status")
    if status and status in protected_statuses.get(doc.doctype, set()):
        frappe.throw(_("Cannot delete {0} in status {1}. Use the controlled cancellation, closing, or revocation action instead.").format(doc.doctype, status))
