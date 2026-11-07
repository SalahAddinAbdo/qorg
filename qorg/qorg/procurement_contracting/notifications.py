import frappe
from qorg.qorg.procurement_contracting.communications import provision_email_templates

STATUS_NOTIFICATIONS=[
 ("QOrg Procurement - Approved Purchase Request","Material Request","docstatus","1","Approved Purchase Request","owner"),
 ("QOrg Procurement - Process Assignment","Procurement Process","status","Draft Setup","Procurement Process Assignment","owner"),
 ("QOrg Procurement - Process Setup Approved","Procurement Process","status","Setup Approved","Procurement Process Assignment","Procurement Manager"),
 ("QOrg Procurement - Submission Received","Procurement Submission","submission_status","Submitted","Bid Submission Receipt","owner"),
 ("QOrg Procurement - Supplier Information Required","Supplier Registration","registration_status","Submitted","Supplier Information Request","owner"),
 ("QOrg Procurement - Supplier Approved","Supplier Registration","registration_status","Approved","Supplier Profile Approved","owner"),
 ("QOrg Procurement - Supplier Rejected","Supplier Registration","registration_status","Rejected","Supplier Profile Rejected","owner"),
 ("QOrg Procurement - Recommendation Ready","Procurement Process","status","Combined Evaluation Completed","Award Recommendation Submitted","Procurement Award Approver"),
 ("QOrg Procurement - Award Approved","Procurement Process","status","Award Approved","Award Notification","Procurement Manager"),
 ("QOrg Procurement - Contract Approval","Procurement Contract","status","Under Approval","Contract Approval Required","Procurement Manager"),
 ("QOrg Procurement - Contract Active","Procurement Contract","status","Active","Contract Activated","contract_manager"),
]

def _message(template_name):
 return "<div style='font-family:Arial,sans-serif'><p><b>"+template_name+"</b></p><p>{{ doc.name }} | {{ doc.status or doc.submission_status or doc.registration_status or '' }}</p><p><a href='{{ frappe.utils.get_url_to_form(doc.doctype, doc.name) }}'>Open Record | فتح السجل</a></p></div>"

def provision_notifications():
 provision_email_templates()
 for name,doctype,field,value,template,receiver in STATUS_NOTIFICATIONS:
  existing=frappe.db.exists("Notification",name);doc=frappe.get_doc("Notification",name) if existing else frappe.new_doc("Notification")
  doc.name=name;doc.subject=frappe.db.get_value("Email Template",template,"subject") or template;doc.document_type=doctype;doc.channel="Email";doc.enabled=1;doc.message=_message(template)
  # Value Change prevents repeat sends on unrelated saves.
  doc.event="Value Change";doc.value_changed=field;doc.condition=f"doc.{field} == {value!r}" if field!="docstatus" else "doc.docstatus == 1"
  doc.set("recipients",[])
  if receiver in ("owner","contract_manager"):
   doc.append("recipients",{"receiver_by_document_field":receiver})
  else:
   doc.append("recipients",{"receiver_by_role":receiver})
  doc.save(ignore_permissions=True) if existing else doc.insert(ignore_permissions=True)
