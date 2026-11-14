import frappe
from qorg.qorg.procurement_contracting.communications import upsert_templates, provision_email_templates

SPECS = [
 ("Procurement - Approved Purchase Request","Material Request","docstatus",1,"Approved Purchase Request","Procurement Officer"),
 ("Procurement - Process Assignment","Procurement Process","status","Draft","Procurement Process Assignment","Procurement Officer"),
 ("Procurement - Bid Submission Receipt","Procurement Submission","submission_status","Submitted","Bid Submission Receipt","owner"),
 ("Procurement - Contract Approval","Procurement Contract","status","Under Approval","Contract Approval Required","Procurement Manager"),
 ("Procurement - Contract Activated","Procurement Contract","status","Active","Contract Activated","contract_manager"),
]

def provision():
 upsert_templates()
 body_field="response" if frappe.get_meta("Email Template").has_field("response") else "response_html"
 for name,doctype,field,value,template,receiver in SPECS:
  if not frappe.db.exists("DocType",doctype):continue
  template_doc=frappe.get_doc("Email Template",template)
  exists=frappe.db.exists("Notification",name);doc=frappe.get_doc("Notification",name) if exists else frappe.new_doc("Notification")
  if not exists:doc.name=name
  doc.document_type=doctype;doc.channel="Email";doc.enabled=1;doc.event="Value Change";doc.value_changed=field
  doc.condition=f"doc.{field} == {value!r}" if field!="docstatus" else f"doc.docstatus == {value}"
  doc.subject=template_doc.subject;doc.message=template_doc.get(body_field) or "";doc.set("recipients",[])
  if receiver in {"owner", "contract_manager", "recipient_user"}:
   doc.append("recipients", {"receiver_by_document_field": receiver})
  else:
   if not frappe.db.exists("Role", receiver):
    frappe.throw(f"Managed procurement notification {name} references missing role {receiver}.")
   doc.append("recipients", {"receiver_by_role": receiver})
  doc.save(ignore_permissions=True) if exists else doc.insert(ignore_permissions=True)
  frappe.db.set_value("Notification", name, {"subject": template_doc.subject, "message": template_doc.get(body_field) or ""}, update_modified=False)

# Backward-compatible entry point used by procurement provisioning.
provision_notifications = provision
