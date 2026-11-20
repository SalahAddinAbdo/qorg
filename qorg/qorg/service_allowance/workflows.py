from __future__ import annotations
import frappe
from qorg.qorg.enterprise_foundation.workflow_manager import ensure_managed_workflow

ROLES=("Accounts User","Accounts Manager","Projects Manager","System Manager")
STATES=(("Draft","Info"),("Under Review","Warning"),("Approved","Success"),("Rejected","Danger"),("Cancelled","Danger"))
ACTIONS=("Submit for Review","Approve","Return to Draft","Reject","Reopen","Cancel")

def provision_cost_workflows():
    for role in ROLES:
        if not frappe.db.exists("Role",role):frappe.get_doc({"doctype":"Role","role_name":role}).insert(ignore_permissions=True)
    for name,style in STATES:
        if not frappe.db.exists("Workflow State",name):frappe.get_doc({"doctype":"Workflow State","workflow_state_name":name,"style":style}).insert(ignore_permissions=True)
    for action in ACTIONS:
        if not frappe.db.exists("Workflow Action Master",action):frappe.get_doc({"doctype":"Workflow Action Master","workflow_action_name":action}).insert(ignore_permissions=True)
    common_states=[
      {"state":"Draft","doc_status":"0","allow_edit":"Accounts User"},
      {"state":"Under Review","doc_status":"0","allow_edit":"Accounts Manager"},
      {"state":"Approved","doc_status":"1","allow_edit":"Accounts Manager"},
      {"state":"Rejected","doc_status":"0","allow_edit":"Accounts User"},
      {"state":"Cancelled","doc_status":"2","allow_edit":"Accounts Manager"},
    ]
    transitions=[
      {"state":"Draft","action":"Submit for Review","next_state":"Under Review","allowed":"Accounts User","allow_self_approval":0},
      {"state":"Under Review","action":"Approve","next_state":"Approved","allowed":"Accounts Manager","allow_self_approval":0},
      {"state":"Under Review","action":"Return to Draft","next_state":"Draft","allowed":"Accounts Manager","allow_self_approval":1},
      {"state":"Under Review","action":"Reject","next_state":"Rejected","allowed":"Accounts Manager","allow_self_approval":1},
      {"state":"Rejected","action":"Reopen","next_state":"Draft","allowed":"Accounts User","allow_self_approval":1},
      {"state":"Approved","action":"Cancel","next_state":"Cancelled","allowed":"Accounts Manager","allow_self_approval":0},
    ]
    workflow_specs=(
      ("Shared Cost Allocation Run","Shared Cost Allocation Run Approval",[row for row in transitions if not (row["state"]=="Approved" and row["action"]=="Cancel")]),
      ("Service and Allowance Accrual","Service and Allowance Accrual Approval",transitions),
    )
    for doctype,title,doctype_transitions in workflow_specs:
        for old in frappe.get_all("Workflow",filters={"document_type":doctype,"is_active":1,"workflow_name":["!=",title]},pluck="name"):
            frappe.db.set_value("Workflow",old,"is_active",0,update_modified=False)
        ensure_managed_workflow({"workflow_name":title,"document_type":doctype,"is_active":1,"workflow_state_field":"workflow_state","send_email_alert":0,"states":common_states,"transitions":doctype_transitions},version="1.1.0")
