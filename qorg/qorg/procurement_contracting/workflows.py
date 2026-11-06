import frappe
WORKFLOWS={
 "Procurement Process":[("Draft Setup","Setup Approved","Approve Setup","Procurement Manager"),("Setup Approved","Published or Invited","Publish or Invite","Procurement Officer"),("Published or Invited","Submission Closed","Close Submissions","Procurement Officer"),("Submission Closed","Opening Completed","Complete Opening","Bid Opening Committee Member"),("Opening Completed","Technical Evaluation Approved","Approve Technical Evaluation","Technical Evaluation Committee Member"),("Technical Evaluation Approved","Financial Evaluation Approved","Approve Financial Evaluation","Financial Evaluation Committee Member"),("Financial Evaluation Approved","Combined Evaluation Completed","Complete Evaluation Summary","Main Procurement Committee Member"),("Combined Evaluation Completed","Award Approved","Approve Award","Procurement Award Approver"),("Award Approved","Closed","Close Process","Procurement Manager")],
 "Supplier Registration":[("Draft","Submitted","Submit for Review","Website User"),("Submitted","Under Review","Start Review","Procurement Officer"),("Under Review","Approved","Approve Supplier","Procurement Manager"),("Under Review","Additional Information Required","Request Information","Procurement Officer")],
 "Procurement Contract":[("Draft","Under Approval","Submit for Approval","Contract Manager"),("Under Approval","Active","Approve Contract","Procurement Manager"),("Active","Completed","Complete Contract","Contract Manager"),("Active","Terminated","Terminate Contract","Procurement Manager")],
}
def provision_workflows():
 for doctype,transitions in WORKFLOWS.items():
  if frappe.db.exists("Workflow",{"document_type":doctype,"is_active":1}): continue
  name=f"QOrg {doctype} Workflow"
  states=[]
  for src,dst,action,role in transitions:
   for st in (src,dst):
    if st not in states: states.append(st)
  doc=frappe.get_doc({"doctype":"Workflow","workflow_name":name,"document_type":doctype,"is_active":1,"workflow_state_field":"workflow_state","send_email_alert":0})
  for i,st in enumerate(states): doc.append("states",{"state":st,"doc_status":0 if i<len(states)-1 else 1,"allow_edit":"Procurement Manager"})
  for src,dst,action,role in transitions: doc.append("transitions",{"state":src,"action":action,"next_state":dst,"allowed":role,"allow_self_approval":0})
  doc.insert(ignore_permissions=True)
