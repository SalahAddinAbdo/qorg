import frappe

SPECS = [
    ("Inventory - Receipt Inspection Required", "Purchase Receipt", "custom_receipt_acceptance_status", "Pending Inspection", "Receipt Inspection Required", "Stock Manager"),
    ("Inventory - Handover Pending", "Stock Handover", "handover_status", "Pending Handover", "Stock Handover Notice", "recipient_user"),
    ("Inventory - Handover Discrepancy", "Stock Handover", "handover_status", "Discrepancy Review", "Handover Discrepancy Notice", "Stock Manager"),
    ("Inventory - Incident Decision Pending", "Asset Incident", "incident_status", "Decision Pending", "Incident Decision Pending", "Asset Manager"),
    ("Inventory - Verification Approval Pending", "Physical Verification", "approval_status", "Pending Approval", "Verification Approval Pending", "Stock Manager"),
]


def provision_notifications():
    body_field = "response" if frappe.get_meta("Email Template").has_field("response") else "response_html"
    for name, doctype, field, value, template, receiver in SPECS:
        if not frappe.db.exists("DocType", doctype):
            continue
        template_doc = frappe.get_doc("Email Template", template)
        existing = frappe.db.exists("Notification", name)
        doc = frappe.get_doc("Notification", name) if existing else frappe.new_doc("Notification")
        if not existing:
            doc.name = name
        doc.document_type = doctype
        doc.channel = "Email"
        doc.enabled = 1
        doc.event = "Value Change"
        doc.value_changed = field
        doc.condition = f"doc.{field} == {value!r}"
        doc.subject = template_doc.subject
        doc.message = template_doc.get(body_field) or ""
        doc.set("recipients", [])
        if receiver in {"recipient_user"}:
            doc.append("recipients", {"receiver_by_document_field": receiver})
        else:
            doc.append("recipients", {"receiver_by_role": receiver})
        doc.save(ignore_permissions=True) if existing else doc.insert(ignore_permissions=True)
