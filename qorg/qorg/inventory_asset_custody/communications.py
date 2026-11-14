import frappe
from qorg.qorg.procurement_contracting.communications import TEMPLATES, body

INVENTORY_TEMPLATE_NAMES = {
    "Receipt Inspection Required", "Receipt Acceptance Notice", "Stock Handover Notice",
    "Handover Discrepancy Notice", "Custody Assignment Notice", "Custody Return Reminder",
    "Asset Custody Notice", "Asset Incident Notice", "Inspection Due Reminder",
    "Incident Decision Pending", "Verification Approval Pending", "Verification Approval Notice",
}


def provision_communications():
    body_field = "response" if frappe.get_meta("Email Template").has_field("response") else "response_html"
    for name in INVENTORY_TEMPLATE_NAMES:
        if name not in TEMPLATES:
            continue
        subject, lead_en, lead_ar = TEMPLATES[name]
        existing = frappe.db.exists("Email Template", name)
        doc = frappe.get_doc("Email Template", name) if existing else frappe.new_doc("Email Template")
        if not existing:
            doc.name = name
        doc.subject = subject + " - {{ doc.name }}"
        doc.use_html = 1
        doc.set(body_field, body(subject.split(" | ")[0], subject.split(" | ")[-1], lead_en, lead_ar))
        doc.save(ignore_permissions=True) if existing else doc.insert(ignore_permissions=True)
    from qorg.qorg.inventory_asset_custody.notifications import provision_notifications
    provision_notifications()
