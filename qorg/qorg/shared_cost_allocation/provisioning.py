import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

VERSION = "2.0.0"
ROLES = ("Shared Cost Allocation Manager", "Shared Cost Allocation User")
CUSTOM_FIELDS = {
    "Company": [
        {"fieldname":"custom_shared_cost_settings_section","label":"Shared and Indirect Cost Allocation","fieldtype":"Section Break","insert_after":"default_finance_book"},
        {"fieldname":"custom_enable_shared_cost_allocation","label":"Enable Shared Cost Allocation","fieldtype":"Check","default":"0","insert_after":"custom_shared_cost_settings_section"},
        {"fieldname":"custom_shared_cost_default_cost_center","label":"Default Shared Cost Center","fieldtype":"Link","options":"Cost Center","insert_after":"custom_enable_shared_cost_allocation"},
        {"fieldname":"custom_shared_cost_column","fieldtype":"Column Break","insert_after":"custom_shared_cost_default_cost_center"},
        {"fieldname":"custom_indirect_cost_expense_account","label":"Default Indirect Cost Expense Account","fieldtype":"Link","options":"Account","insert_after":"custom_shared_cost_column"},
        {"fieldname":"custom_indirect_cost_recovery_account","label":"Default Indirect Cost Recovery Account","fieldtype":"Link","options":"Account","insert_after":"custom_indirect_cost_expense_account"},
        {"fieldname":"custom_payroll_account_group","label":"Payroll Account Group","fieldtype":"Link","options":"Account","insert_after":"custom_indirect_cost_recovery_account"},
        {"fieldname":"custom_shared_cost_closeout_section","label":"Allocation Closeout Controls","fieldtype":"Section Break","insert_after":"custom_payroll_account_group"},
        {"fieldname":"custom_require_allocation_before_project_closeout","label":"Require Allocation Completion Before Project Closeout","fieldtype":"Check","default":"1","insert_after":"custom_shared_cost_closeout_section"},
        {"fieldname":"custom_allow_post_closeout_adjustment","label":"Allow Donor-Approved Post-Closeout Adjustment","fieldtype":"Check","default":"0","insert_after":"custom_require_allocation_before_project_closeout"},
    ],
    "Project Closure": [
        {"fieldname":"custom_cost_allocation_section","label":"Shared and Indirect Cost Closeout","fieldtype":"Section Break","insert_after":"grant_closeout_completed"},
        {"fieldname":"custom_pending_allocation_runs","label":"Pending Allocation Runs","fieldtype":"Int","read_only":1,"insert_after":"custom_cost_allocation_section"},
        {"fieldname":"custom_unrecovered_indirect_cost","label":"Unrecovered Indirect Cost","fieldtype":"Currency","read_only":1,"insert_after":"custom_pending_allocation_runs"},
        {"fieldname":"custom_cost_allocation_closeout_status","label":"Cost Allocation Closeout Status","fieldtype":"Select","options":"Not Assessed\nPending\nComplete\nNot Applicable","default":"Not Assessed","insert_after":"custom_unrecovered_indirect_cost"},
    ],
}

def _create_custom_fields():
    try:
        from qorg.qorg.custom_fields import create_custom_fields_if_changed
        create_custom_fields_if_changed(CUSTOM_FIELDS, update=True)
    except ImportError:
        create_custom_fields(CUSTOM_FIELDS, update=True)

def _role(name):
    if not frappe.db.exists("Role", name):
        frappe.get_doc({"doctype":"Role","role_name":name,"desk_access":1}).insert(ignore_permissions=True)

def _workflow(name, doctype, states, transitions):
    for state, style, docstatus, role in states:
        if not frappe.db.exists("Workflow State", state):
            frappe.get_doc({"doctype":"Workflow State","workflow_state_name":state,"style":style}).insert(ignore_permissions=True)
    for action, source, target, role in transitions:
        if not frappe.db.exists("Workflow Action Master", action):
            frappe.get_doc({"doctype":"Workflow Action Master","workflow_action_name":action}).insert(ignore_permissions=True)
    exists=frappe.db.exists("Workflow", name); doc=frappe.get_doc("Workflow",name) if exists else frappe.new_doc("Workflow")
    if not exists: doc.workflow_name=name
    doc.document_type=doctype; doc.is_active=1; doc.workflow_state_field="status" if doctype.endswith("Rule") else "run_status"; doc.send_email_alert=0
    doc.set("states",[]); doc.set("transitions",[])
    for state,style,docstatus,role in states: doc.append("states",{"state":state,"doc_status":docstatus,"allow_edit":role})
    for action,source,target,role in transitions: doc.append("transitions",{"action":action,"state":source,"next_state":target,"allowed":role,"allow_self_approval":0})
    doc.save(ignore_permissions=True) if exists else doc.insert(ignore_permissions=True)

def provision_shared_cost_allocation():
    for role in ROLES: _role(role)
    _create_custom_fields()
    _workflow("Shared Cost Rule Approval","Shared Cost Allocation Rule",[("Draft","Warning",0,"Shared Cost Allocation User"),("Active","Success",1,"Shared Cost Allocation Manager"),("Cancelled","Danger",2,"Shared Cost Allocation Manager")],[("Approve","Draft","Active","Shared Cost Allocation Manager"),("Cancel","Active","Cancelled","Shared Cost Allocation Manager")])
    _workflow("Shared Cost Run Approval","Shared Cost Allocation Run",[("Draft","Warning",0,"Shared Cost Allocation User"),("Previewed","Info",0,"Shared Cost Allocation User"),("Posted","Success",1,"Shared Cost Allocation Manager"),("Reversed","Danger",2,"Shared Cost Allocation Manager")],[("Preview","Draft","Previewed","Shared Cost Allocation User"),("Submit","Previewed","Posted","Shared Cost Allocation Manager"),("Cancel","Posted","Reversed","Shared Cost Allocation Manager")])
    _notifications()
    frappe.clear_cache()
    return {"version":VERSION,"roles":ROLES,"custom_fields":list(CUSTOM_FIELDS)}


def _notifications():
    records=[
        {"name":"Shared Cost Allocation Requires Review","document_type":"Shared Cost Allocation Run","event":"Value Change","value_changed":"run_status","condition":"doc.run_status == 'Previewed' and (doc.unallocated_amount or doc.over_budget_entries)","subject":"Allocation run {{ doc.name }} requires review","message":"Review unallocated amounts, budget exceptions and eligibility before submission.","recipients":[{"receiver_by_role":"Shared Cost Allocation Manager"}]},
        {"name":"Shared Cost Adjustment Approval Reference Missing","document_type":"Shared Cost Allocation Run","event":"Save","condition":"doc.run_type == 'Adjustment' and not doc.donor_approval_reference","subject":"Adjustment run {{ doc.name }} requires donor approval reference","message":"Complete the donor approval reference before approval.","recipients":[{"receiver_by_role":"Shared Cost Allocation Manager"}]},
    ]
    for spec in records:
        if frappe.db.exists("Notification",spec["name"]): continue
        doc=frappe.new_doc("Notification");doc.update({"name":spec["name"],"subject":spec["subject"],"document_type":spec["document_type"],"event":spec["event"],"condition":spec["condition"],"message":spec["message"],"enabled":1,"channel":"System Notification"})
        if spec.get("value_changed"):doc.value_changed=spec["value_changed"]
        for row in spec["recipients"]:doc.append("recipients",row)
        doc.insert(ignore_permissions=True)
