from __future__ import annotations

import frappe


SPECS = (
    ("Inventory - Receipt Inspection Required", "Purchase Receipt", "custom_receipt_acceptance_status", "Pending Inspection", "Receipt Inspection Required", "Stock Manager"),
    ("Inventory - Handover Pending", "Stock Handover", "handover_status", "Pending Handover", "Stock Handover Notice", "recipient_user"),
    ("Inventory - Handover Discrepancy", "Stock Handover", "handover_status", "Discrepancy Review", "Handover Discrepancy Notice", "Stock Manager"),
    ("Inventory - Incident Decision Pending", "Asset Incident", "incident_status", "Decision Pending", "Incident Decision Pending", "Asset Manager"),
    ("Inventory - Verification Approval Pending", "Physical Verification", "approval_status", "Pending Approval", "Verification Approval Pending", "Stock Manager"),
)

# Exact predecessors duplicated in the exported site data. The Inventory-prefixed records above are authoritative.
LEGACY_NOTIFICATIONS = (
    "Verification Approval Pending",
    "Incident Decision Pending",
    "Handover Discrepancy Review",
    "Handover Acknowledgement Pending",
    "Receipt Inspection Required",
)


def _delete_legacy_notifications() -> list[str]:
    deleted = []
    for name in LEGACY_NOTIFICATIONS:
        if frappe.db.exists("Notification", name):
            frappe.delete_doc("Notification", name, ignore_permissions=True, force=True)
            deleted.append(name)
    return deleted


def _template_body(template_doc) -> str:
    for fieldname in ("response_html", "response"):
        if template_doc.meta.has_field(fieldname) and template_doc.get(fieldname):
            return template_doc.get(fieldname)
    return ""


def provision_notifications():
    deleted = _delete_legacy_notifications()
    created = []
    updated = []
    notification_meta = frappe.get_meta("Notification")

    for name, doctype, field, value, template, receiver in SPECS:
        if not frappe.db.exists("DocType", doctype):
            continue
        if not frappe.db.exists("Email Template", template):
            frappe.throw(f"Managed inventory notification {name} references missing Email Template {template}.")

        template_doc = frappe.get_doc("Email Template", template)
        body = _template_body(template_doc)
        if not template_doc.subject or not body:
            frappe.throw(f"Managed Email Template {template} must have a subject and bilingual HTML body.")

        exists = frappe.db.exists("Notification", name)
        doc = frappe.get_doc("Notification", name) if exists else frappe.new_doc("Notification")
        if not exists:
            doc.name = name
        doc.document_type = doctype
        doc.channel = "Email"
        doc.enabled = 1
        doc.event = "Value Change"
        doc.value_changed = field
        doc.condition = f"doc.{field} == {value!r}"
        doc.subject = template_doc.subject
        doc.message_type = "HTML"
        doc.message = body
        if notification_meta.has_field("email_template"):
            doc.email_template = template
        doc.set("recipients", [])

        if receiver == "recipient_user":
            doc.append("recipients", {"receiver_by_document_field": receiver})
        else:
            if not frappe.db.exists("Role", receiver):
                frappe.throw(f"Managed inventory notification {name} references missing role {receiver}.")
            doc.append("recipients", {"receiver_by_role": receiver})

        if exists:
            doc.save(ignore_permissions=True)
            updated.append(name)
        else:
            doc.insert(ignore_permissions=True)
            created.append(name)

    return {"created": created, "updated": updated, "deleted_legacy": deleted}
