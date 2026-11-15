from __future__ import annotations
import frappe
from .communications import provision_templates
SPECS=(
 ("Finance - Funding Agreement Action Required","Under Review","Funding Agreement Action Required","Projects Manager"),
 ("Finance - Funding Agreement Activated","Active","Funding Agreement Action Required","Accounts Manager"),
 ("Finance - Funding Agreement Closeout Exception","Closing","Financial Control Exception","Accounts Manager"),
)
OLD_NAMES=("Finance - Funding Agreement Review Required","Finance - Funding Agreement Closeout Required")
def provision_notifications():
 result={"templates":provision_templates(),"created":[],"updated":[],"disabled":[]}; nmeta=frappe.get_meta("Notification"); fmeta=frappe.get_meta("Funding Agreement")
 for name,value,template,role in SPECS:
  if not frappe.db.exists("Role",role): frappe.throw(f"Required existing role is missing: {role}")
  t=frappe.get_doc("Email Template",template); exists=frappe.db.exists("Notification",name); doc=frappe.get_doc("Notification",name) if exists else frappe.new_doc("Notification")
  if not exists: doc.name=name
  doc.document_type="Funding Agreement"; doc.channel="Email"; doc.enabled=1; doc.event="Value Change"; doc.value_changed="status"; doc.condition=f"doc.status == {value!r}"; doc.subject=t.subject; doc.message_type="HTML"; doc.message=t.response
  if nmeta.has_field("email_template"): doc.email_template=template
  doc.set("recipients",[])
  if fmeta.has_field("custom_current_responsible_user"): doc.append("recipients",{"receiver_by_document_field":"custom_current_responsible_user"})
  else: doc.append("recipients",{"receiver_by_role":role})
  doc.save(ignore_permissions=True) if exists else doc.insert(ignore_permissions=True); result["updated" if exists else "created"].append(name)
 for name in OLD_NAMES:
  if frappe.db.exists("Notification",name): frappe.db.set_value("Notification",name,"enabled",0,update_modified=False); result["disabled"].append(name)
 return result
