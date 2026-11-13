import frappe
STATES=(('Pending Handover','Orange'),('Acknowledged','Green'),('Discrepancy Review','Red'),('Active Custody','Blue'),('Returned','Green'),('Under Investigation','Orange'),('Decision Pending','Yellow'),('Resolved','Green'),('Counting','Blue'),('Recount Required','Orange'),('Pending Approval','Yellow'),('Approved','Green'))
def provision_workflows():
 for name,style in STATES:
  if not frappe.db.exists('Workflow State',name):frappe.get_doc({'doctype':'Workflow State','workflow_state_name':name,'style':style}).insert(ignore_permissions=True)
 defs={
 'Stock Handover Approval':('Stock Handover',[('Draft',0,'Stock User'),('Pending Handover',0,'Stock User'),('Acknowledged',1,'Stock Manager'),('Discrepancy Review',0,'Stock Manager')],[('Draft','Prepare Handover','Pending Handover','Stock User',''),('Pending Handover','Acknowledge','Acknowledged','Stock Manager','doc.fully_acknowledged == 1'),('Pending Handover','Review Discrepancy','Discrepancy Review','Stock Manager',"doc.discrepancy_status == 'Open'")]),
 'Asset Custody Approval':('Asset Custody',[('Draft',0,'Asset User'),('Pending Handover',0,'Asset User'),('Active Custody',1,'Asset Manager'),('Returned',1,'Asset Manager')],[('Draft','Prepare Handover','Pending Handover','Asset User',''),('Pending Handover','Activate Custody','Active Custody','Asset Manager','doc.recipient_declaration == 1'),('Active Custody','Confirm Return','Returned','Asset Manager','doc.actual_return_date')]),
 'Incident Resolution':('Asset Incident',[('Draft',0,'Stock User'),('Under Investigation',0,'Stock Manager'),('Decision Pending',0,'Stock Manager'),('Resolved',1,'Stock Manager')],[('Draft','Start Investigation','Under Investigation','Stock Manager',''),('Under Investigation','Submit Decision','Decision Pending','Stock Manager',"doc.decision != 'Pending'"),('Decision Pending','Resolve','Resolved','Stock Manager',"doc.decision != 'Pending'")]),
 'Verification Approval':('Physical Verification',[('Draft',0,'Stock User'),('Counting',0,'Stock User'),('Recount Required',0,'Stock User'),('Pending Approval',0,'Stock Manager'),('Approved',1,'Stock Manager')],[('Draft','Start Counting','Counting','Stock User',''),('Counting','Request Recount','Recount Required','Stock Manager',''),('Counting','Submit for Approval','Pending Approval','Stock User','doc.recount_required == 0'),('Recount Required','Complete Recount','Pending Approval','Stock User','doc.recount_required == 0'),('Pending Approval','Approve','Approved','Stock Manager','doc.snapshot_locked == 1')])}
 for name,(dt,states,transitions) in defs.items():
  if frappe.db.exists('Workflow',name):continue
  d=frappe.get_doc({'doctype':'Workflow','workflow_name':name,'document_type':dt,'is_active':1,'send_email_alert':0,'workflow_state_field':'workflow_state'})
  for state,status,role in states:d.append('states',{'state':state,'doc_status':status,'allow_edit':role})
  for state,action,next_state,role,condition in transitions:
   row={'state':state,'action':action,'next_state':next_state,'allowed':role,'condition':condition,'allow_self_approval':0}
   if frappe.get_meta('Workflow Transition').has_field('custom_responsibility_routing'): row['custom_responsibility_routing']='Clear Responsibility' if next_state in {'Acknowledged','Returned','Resolved','Approved'} else 'Select Next User'
   d.append('transitions',row)
  d.insert(ignore_permissions=True)
