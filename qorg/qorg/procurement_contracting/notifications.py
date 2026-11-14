from __future__ import annotations

import frappe

from qorg.qorg.procurement_contracting.communications import provision_email_templates


SPECS = (
    ("Procurement - Approved Purchase Request", "Material Request", "docstatus", 1, "Approved Purchase Request", "Procurement Officer"),
    ("Procurement - Process Assignment", "Procurement Process", "status", "Draft", "Procurement Process Assignment", "Procurement Officer"),
    ("Procurement - Bid Submission Receipt", "Procurement Submission", "submission_status", "Submitted", "Bid Submission Receipt", "owner"),
    ("Procurement - Contract Approval", "Procurement Contract", "status", "Under Approval", "Contract Approval Required", "Procurement Manager"),
    ("Procurement - Contract Activated", "Procurement Contract", "status", "Active", "Contract Activated", "contract_manager"),
)

# Exact application-owned predecessors and duplicates found in the exported Notification records.
LEGACY_NOTIFICATIONS = (
    "QOrg Procurement - Contract Approval",
    "QOrg Procurement - Recommendation Ready",
    "QOrg Procurement - Supplier Rejected",
    "QOrg Procurement - Supplier Approved",
    "QOrg Procurement - Supplier Information Required",
    "QOrg Procurement - Process Assignment",
    "QOrg Procurement - Contract Active",
    "QOrg Procurement - Award Approved",
    "QOrg Procurement - Technical Approved",
    "QOrg Procurement - Submission Received",
    "QOrg Procurement - Process Setup Approved",
    "QOrg Procurement - Approved Purchase Request",
    "QOrg - Contract Expiry Reminder",
    "QOrg - Award Decision Required",
    "QOrg - Approved Purchase Request Assigned",
)

DOCUMENT_RECIPIENT_FIELDS = {"owner", "contract_manager", "recipient_user"}


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


def provision():
    provision_email_templates()
    deleted = _delete_legacy_notifications()
    created = []
    updated = []

    notification_meta = frappe.get_meta("Notification")
    for name, doctype, field, value, template, receiver in SPECS:
        if not frappe.db.exists("DocType", doctype):
            continue
        if not frappe.db.exists("Email Template", template):
            frappe.throw(f"Managed procurement notification {name} references missing Email Template {template}.")

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
        doc.condition = f"doc.{field} == {value!r}" if field != "docstatus" else f"doc.docstatus == {value}"
        doc.subject = template_doc.subject
        doc.message_type = "HTML"
        doc.message = body
        if notification_meta.has_field("email_template"):
            doc.email_template = template
        doc.set("recipients", [])

        if receiver in DOCUMENT_RECIPIENT_FIELDS:
            doc.append("recipients", {"receiver_by_document_field": receiver})
        else:
            if not frappe.db.exists("Role", receiver):
                frappe.throw(f"Managed procurement notification {name} references missing role {receiver}.")
            doc.append("recipients", {"receiver_by_role": receiver})

        if exists:
            doc.save(ignore_permissions=True)
            updated.append(name)
        else:
            doc.insert(ignore_permissions=True)
            created.append(name)

    return {"created": created, "updated": updated, "deleted_legacy": deleted}


provision_notifications = provision
