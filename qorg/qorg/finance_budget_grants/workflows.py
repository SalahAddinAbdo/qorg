from __future__ import annotations
import frappe
STATES=(("Draft","Info",0,"Projects Manager"),("Under Review","Warning",0,"Projects Manager"),("Rejected","Danger",0,"Projects Manager"),("Active","Success",1,"Accounts Manager"),("Suspended","Warning",1,"Accounts Manager"),("Closing","Warning",1,"Accounts Manager"),("Closed","Success",1,"Accounts Manager"),("Cancelled","Danger",2,"Accounts Manager"))
ROLES=("Accounts Manager","Projects Manager","System Manager")
TRANSITIONS=(
 ("Submit for Review","Draft","Under Review","Projects Manager"),
 ("Activate","Under Review","Active","Accounts Manager"),
 ("Return to Draft","Under Review","Draft","Projects Manager"),
 ("Reject","Under Review","Rejected","Projects Manager"),
 ("Reopen","Rejected","Draft","Projects Manager"),
 ("Suspend","Active","Suspended","Accounts Manager"),
 ("Resume","Suspended","Active","Accounts Manager"),
 ("Start Closeout","Active","Closing","Projects Manager"),
 ("Return to Active","Closing","Active","Accounts Manager"),
 ("Close","Closing","Closed","Accounts Manager"),
 ("Cancel","Active","Cancelled","Accounts Manager"),
 ("Cancel","Suspended","Cancelled","Accounts Manager"),
 ("Cancel","Closing","Cancelled","Accounts Manager"),

)
def provision_workflow():
 for role in ROLES:
  if not frappe.db.exists("Role",role): frappe.throw(f"Required existing role is missing: {role}")
 for action,source,target,role in TRANSITIONS:
  if not frappe.db.exists("Workflow Action Master",action): frappe.get_doc({"doctype":"Workflow Action Master","workflow_action_name":action}).insert(ignore_permissions=True)
 for name,style,docstatus,role in STATES:
  exists=frappe.db.exists("Workflow State",name); state=frappe.get_doc("Workflow State",name) if exists else frappe.new_doc("Workflow State")
  if not exists: state.workflow_state_name=name
  if not exists:
   state.style=style
   state.insert(ignore_permissions=True)
 name="Funding Agreement Approval"; exists=frappe.db.exists("Workflow",name); doc=frappe.get_doc("Workflow",name) if exists else frappe.new_doc("Workflow")
 if not exists: doc.workflow_name=name
 doc.document_type="Funding Agreement"; doc.is_active=1; doc.workflow_state_field="status"; doc.send_email_alert=0
 doc.set("states",[]); doc.set("transitions",[])
 transition_meta=frappe.get_meta("Workflow Transition")
 for state,style,docstatus,role in STATES: doc.append("states",{"state":state,"doc_status":docstatus,"allow_edit":role})
 for action,source,target,role in TRANSITIONS:
  values={"action":action,"state":source,"next_state":target,"allowed":role,"allow_self_approval":0}
  if transition_meta.has_field("custom_responsibility_routing"): values["custom_responsibility_routing"]="Keep Current Responsible"
  doc.append("transitions",values)
 doc.save(ignore_permissions=True) if exists else doc.insert(ignore_permissions=True)
 return name
