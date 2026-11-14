from __future__ import annotations
import frappe
from qorg.qorg.enterprise_foundation.idempotent_provisioning import create_custom_fields_if_changed
MODULE='QOrg'
def f(n,l,t='Data',o=None,**kw):
 d={'fieldname':n,'label':l,'fieldtype':t,'is_system_generated':1,'module':MODULE}
 if o:d['options']=o
 d.update(kw);return d
def add(out,dt,rows):
 if frappe.db.exists('DocType',dt):out.setdefault(dt,[]).extend(rows)
def definitions():
 out={}
 # Appropriate standard settings, no separate settings DocType.
 add(out,'Stock Settings',[f('inventory_control_section','Receipt and Issue Controls','Section Break',insert_after='allow_negative_stock'),f('custom_receiving_warehouse','Receiving Warehouse','Link','Warehouse',insert_after='inventory_control_section'),f('custom_quarantine_warehouse','Quarantine Warehouse','Link','Warehouse',insert_after='custom_receiving_warehouse'),f('custom_accepted_warehouse','Accepted Warehouse','Link','Warehouse',insert_after='custom_quarantine_warehouse'),f('inventory_settings_column','','Column Break',insert_after='custom_accepted_warehouse'),f('custom_rejected_warehouse','Rejected Warehouse','Link','Warehouse',insert_after='inventory_settings_column'),f('custom_returns_warehouse','Returns Warehouse','Link','Warehouse',insert_after='custom_rejected_warehouse'),f('custom_damaged_warehouse','Damaged Warehouse','Link','Warehouse',insert_after='custom_returns_warehouse'),f('inventory_rules_section','Inventory Rules','Section Break',insert_after='custom_damaged_warehouse'),f('custom_require_inspection','Require Inspection Before Acceptance','Check',insert_after='inventory_rules_section',default='1'),f('custom_allow_over_receipt','Allow Over Receipt','Check',insert_after='custom_require_inspection',default='0'),f('custom_over_receipt_tolerance','Over Receipt Tolerance Percentage','Percent',insert_after='custom_allow_over_receipt',default='0'),f('custom_require_handover','Require Handover Acknowledgement','Check',insert_after='custom_over_receipt_tolerance',default='1'),f('inventory_rules_column','','Column Break',insert_after='custom_require_handover'),f('custom_allow_emergency_issue','Allow Emergency Issue','Check',insert_after='inventory_rules_column',default='0'),f('custom_require_return_date','Require Temporary Issue Return Date','Check',insert_after='custom_allow_emergency_issue',default='1'),f('custom_custody_reminder_days','Custody Reminder Days','Int',insert_after='custom_require_return_date',default='7'),f('custom_require_variance_approval','Require Variance Approval','Check',insert_after='custom_custody_reminder_days',default='1')])
 add(out,'Asset Settings',[f('custody_control_section','Custody and Disposal Controls','Section Break',insert_after='asset_naming_series'),f('custom_require_custody_acknowledgement','Require Custody Acknowledgement','Check',insert_after='custody_control_section',default='1'),f('custom_prevent_multiple_custodies','Prevent Multiple Active Custodies','Check',insert_after='custom_require_custody_acknowledgement',default='1'),f('asset_control_column','','Column Break',insert_after='custom_prevent_multiple_custodies'),f('custom_require_disposal_approval','Require Donor Disposal Approval','Check',insert_after='asset_control_column',default='1'),f('custom_verification_interval_days','Physical Verification Interval Days','Int',insert_after='custom_require_disposal_approval',default='365')])
 add(out,'Buying Settings',[f('receipt_policy_section','Receipt Acceptance Policy','Section Break',insert_after='allow_item_to_be_added_multiple_times'),f('custom_require_receipt_committee','Require Receipt Committee','Check',insert_after='receipt_policy_section',default='0'),f('custom_receipt_committee_threshold','Receipt Committee Threshold','Currency',insert_after='custom_require_receipt_committee',default='0'),f('custom_require_final_receipt','Require Final Receipt Confirmation','Check',insert_after='custom_receipt_committee_threshold',default='1')])
 add(out,'Purchase Receipt',[f('receipt_trace_section','Receipt and Acceptance','Section Break',insert_after='project',collapsible=1),f('custom_procurement_process','Procurement Process','Link','Procurement Process',insert_after='receipt_trace_section',read_only=1,in_standard_filter=1),f('custom_procurement_contract','Procurement Contract','Link','Procurement Contract',insert_after='custom_procurement_process',read_only=1,no_copy=1,in_standard_filter=1),f('custom_procurement_acceptance','Procurement Acceptance','Link','Procure Acceptance',insert_after='custom_procurement_contract',read_only=1),f('custom_receipt_classification','Receipt Classification','Select','Standard Receipt\nPartial Receipt\nFinal Receipt\nReplacement Receipt\nReturn Receipt\nCorrective Receipt',insert_after='custom_procurement_acceptance',default='Standard Receipt'),f('receipt_trace_column','','Column Break',insert_after='custom_receipt_classification'),f('custom_is_final_receipt','Is Final Receipt','Check',insert_after='receipt_trace_column'),f('custom_receipt_inspection_required','Inspection Required','Check',insert_after='custom_is_final_receipt',default='1'),f('custom_receipt_committee','Receipt Committee','Link','Procure Committee',insert_after='custom_receipt_inspection_required'),f('custom_receipt_acceptance_status','Acceptance Status','Select','Pending Inspection\nUnder Inspection\nPartially Accepted\nAccepted\nRejected\nReplacement Required\nReinspection Required',insert_after='custom_receipt_committee',read_only=1,in_standard_filter=1),f('custom_funding_source','Funding Source','Link','Project Funding Source',insert_after='custom_receipt_acceptance_status',in_standard_filter=1)])
 add(out,'Purchase Receipt Item',[f('receipt_qty_section','Receipt Quantities','Section Break',insert_after='quality_inspection',collapsible=1),f('custom_contracted_qty','Contracted Quantity','Float',insert_after='receipt_qty_section',read_only=1),f('custom_previously_received_qty','Previously Received Quantity','Float',insert_after='custom_contracted_qty',read_only=1),f('custom_accepted_qty','Accepted Quantity','Float',insert_after='custom_previously_received_qty'),f('receipt_qty_column','','Column Break',insert_after='custom_accepted_qty'),f('custom_returned_qty','Returned Quantity','Float',insert_after='receipt_qty_column',read_only=1),f('custom_replacement_pending_qty','Replacement Pending Quantity','Float',insert_after='custom_returned_qty',read_only=1),f('custom_remaining_contract_qty','Remaining Contract Quantity','Float',insert_after='custom_replacement_pending_qty',read_only=1),f('custom_rejection_reason','Rejection Reason','Small Text',insert_after='custom_remaining_contract_qty')])
 add(out,'Quality Inspection',[
  f('inspection_context_section','Inspection Context','Section Break',insert_after='status',collapsible=1),
  f('custom_inspection_category','Inspection Category','Select','Quantitative\nTechnical\nQuality\nSpecification\nVisual\nSite Inspection\nSample Inspection\nService or Work Acceptance',insert_after='inspection_context_section'),
  f('custom_purchase_receipt','Purchase Receipt','Link','Purchase Receipt',insert_after='custom_inspection_category',read_only=1),
  f('custom_purchase_receipt_item','Purchase Receipt Item','Link','Purchase Receipt Item',insert_after='custom_purchase_receipt',read_only=1),
  f('custom_purchase_order','Purchase Order','Link','Purchase Order',insert_after='custom_purchase_receipt_item',read_only=1),
  f('inspection_context_column','','Column Break',insert_after='custom_purchase_order'),
  f('custom_procurement_process','Procurement Process','Link','Procurement Process',insert_after='inspection_context_column',read_only=1),
  f('custom_procurement_contract','Procurement Contract','Link','Procurement Contract',insert_after='custom_procurement_process',read_only=1),
  f('custom_inspection_committee','Inspection Committee','Link','Procure Committee',insert_after='custom_procurement_contract'),
  f('inspection_quantity_section','Quantities and Result','Section Break',insert_after='custom_inspection_committee'),
  f('custom_sample_size','Sample Size','Float',insert_after='inspection_quantity_section'),
  f('custom_inspected_qty','Inspected Quantity','Float',insert_after='custom_sample_size'),
  f('custom_accepted_qty','Accepted Quantity','Float',insert_after='custom_inspected_qty'),
  f('custom_rejected_qty','Rejected Quantity','Float',insert_after='custom_accepted_qty'),
  f('inspection_result_column','','Column Break',insert_after='custom_rejected_qty'),
  f('custom_qorg_result','Inspection Result','Select','Accepted\nAccepted with Minor Observations\nPartially Accepted\nRejected\nReplacement Required\nReinspection Required',insert_after='inspection_result_column'),
  f('custom_release_action','Release Action','Select','Hold in Quarantine\nRelease to Accepted Stock\nMove to Rejected Stock\nReturn to Supplier\nReplacement Required\nReinspection Required',insert_after='custom_qorg_result',read_only=1),
  f('custom_previous_quality_inspection','Previous Quality Inspection','Link','Quality Inspection',insert_after='custom_release_action',depends_on="eval:doc.custom_qorg_result == 'Reinspection Required'",mandatory_depends_on="eval:doc.custom_qorg_result == 'Reinspection Required'"),
  f('custom_reinspection_number','Reinspection Number','Int',insert_after='custom_previous_quality_inspection',read_only=1,default='0'),
  f('inspection_followup_section','Follow-up References','Section Break',insert_after='custom_reinspection_number',collapsible=1),
  f('custom_release_stock_entry','Release Stock Entry','Link','Stock Entry',insert_after='inspection_followup_section',read_only=1),
  f('custom_return_purchase_receipt','Return Purchase Receipt','Link','Purchase Receipt',insert_after='custom_release_stock_entry',read_only=1),
  f('inspection_followup_column','','Column Break',insert_after='custom_return_purchase_receipt'),
  f('custom_replacement_reference','Replacement Reference','Data',insert_after='inspection_followup_column',read_only=1),
  f('inspection_notes_section','Findings and Evidence','Section Break',insert_after='custom_replacement_reference'),
  f('custom_detailed_findings','Detailed Findings','Text Editor',insert_after='inspection_notes_section'),
  f('custom_evidence','Evidence','Attach',insert_after='custom_detailed_findings'),
 ])
 add(out,'Warehouse',[f('warehouse_policy_section','Warehouse Policy','Section Break',insert_after='warehouse_type',collapsible=1),f('custom_warehouse_role','Warehouse Role','Select','General Stock\nReceiving\nQuarantine or Inspection\nAccepted Stock\nRejected Stock\nProject Stock\nReturns\nDamaged Stock\nTransit',insert_after='warehouse_policy_section',default='General Stock',in_standard_filter=1),f('custom_project_restricted','Project Restricted','Check',insert_after='custom_warehouse_role'),f('custom_default_project','Default Project','Link','Project',insert_after='custom_project_restricted'),f('warehouse_policy_column','','Column Break',insert_after='custom_default_project'),f('custom_funding_restricted','Funding Source Restricted','Check',insert_after='warehouse_policy_column'),f('custom_default_funding_source','Default Funding Source','Link','Project Funding Source',insert_after='custom_funding_restricted'),f('custom_issue_allowed','Issue Allowed','Check',insert_after='custom_default_funding_source',default='1'),f('custom_receipt_allowed','Receipt Allowed','Check',insert_after='custom_issue_allowed',default='1'),f('custom_transfer_allowed','Transfer Allowed','Check',insert_after='custom_receipt_allowed',default='1')])
 add(out,'Material Request',[f('issue_context_section','Material Issue Context','Section Break',insert_after='material_request_type',depends_on='eval:doc.material_request_type=="Material Issue"',collapsible=1),f('custom_issue_usage_type','Issue Usage Type','Select','Operational Consumption\nProject Activity\nBeneficiary Distribution\nField Location\nEmployee Use\nTemporary Issue\nPartner Handover\nReplacement\nEmergency Issue',insert_after='issue_context_section'),f('custom_issue_purpose','Issue Purpose','Small Text',insert_after='custom_issue_usage_type'),f('custom_workplan_activity','Project Workplan Activity','Link','Project Workplan Activity',insert_after='custom_issue_purpose'),f('custom_delivery_location','Delivery Location','Small Text',insert_after='custom_workplan_activity'),f('issue_context_column','','Column Break',insert_after='custom_delivery_location'),f('custom_recipient_type','Recipient Type','Select','Employee\nExternal Person\nOrganization\nBeneficiary\nProject Site',insert_after='issue_context_column'),f('custom_recipient_employee','Recipient Employee','Link','Employee',insert_after='custom_recipient_type'),f('custom_required_delivery_date','Required Delivery Date','Date',insert_after='custom_recipient_employee'),f('custom_return_expected','Return Expected','Check',insert_after='custom_required_delivery_date'),f('custom_expected_return_date','Expected Return Date','Date',insert_after='custom_return_expected'),f('custom_issue_status','Issue Status','Select','Not Issued\nPartially Issued\nFully Issued\nReturned\nClosed',insert_after='custom_expected_return_date',read_only=1,in_standard_filter=1)])
 add(out,'Stock Entry',[f('movement_context_section','Movement Context','Section Break',insert_after='purpose',collapsible=1),f('custom_material_request','Material Request','Link','Material Request',insert_after='movement_context_section',in_standard_filter=1),f('custom_stock_handover','Stock Handover','Link','Stock Handover',insert_after='custom_material_request',read_only=1),f('custom_movement_classification','Movement Classification','Select','Internal Transfer\nProject Transfer\nOperational Issue\nBeneficiary Distribution\nTemporary Issue\nReturn to Warehouse\nReturn from Project\nReturn to Supplier\nReplacement Issue\nCorrective Receipt\nEmergency Issue',insert_after='custom_stock_handover'),f('movement_context_column','','Column Break',insert_after='custom_movement_classification'),f('custom_funding_source','Funding Source','Link','Project Funding Source',insert_after='movement_context_column'),f('custom_workplan_activity','Project Workplan Activity','Link','Project Workplan Activity',insert_after='custom_funding_source'),f('custom_recipient_employee','Recipient Employee','Link','Employee',insert_after='custom_workplan_activity'),f('custom_delivery_location','Delivery Location','Small Text',insert_after='custom_recipient_employee'),f('custom_return_against_stock_entry','Return Against Stock Entry','Link','Stock Entry',insert_after='custom_delivery_location')])
 add(out,'Asset',[f('asset_trace_section','Procurement and Custody','Section Break',insert_after='purchase_receipt',collapsible=1),f('custom_procurement_process','Procurement Process','Link','Procurement Process',insert_after='asset_trace_section',read_only=1),f('custom_procurement_contract','Procurement Contract','Link','Procurement Contract',insert_after='custom_procurement_process',read_only=1),f('custom_funding_source','Funding Source','Link','Project Funding Source',insert_after='custom_procurement_contract'),f('custom_donor','Donor','Link','Donor',insert_after='custom_funding_source'),f('asset_trace_column','','Column Break',insert_after='custom_donor'),f('custom_disposal_approval_required','Disposal Approval Required','Check',insert_after='asset_trace_column'),f('custom_disposal_approval_reference','Disposal Approval Reference','Data',insert_after='custom_disposal_approval_required'),f('custom_current_custody','Current Custody','Link','Asset Custody',insert_after='custom_disposal_approval_reference',read_only=1),f('custom_custody_status','Custody Status','Select','Unassigned\nActive\nReturn Due\nOverdue\nReturned\nDamage Review\nLoss Review',insert_after='custom_current_custody',read_only=1)])
 add(out,'Asset Movement',[f('custody_context_section','Custody Context','Section Break',insert_after='purpose',collapsible=1),f('custom_asset_custody','Asset Custody','Link','Asset Custody',insert_after='custody_context_section',read_only=1),f('custom_project','Project','Link','Project',insert_after='custom_asset_custody'),f('custody_context_column','','Column Break',insert_after='custom_project'),f('custom_funding_source','Funding Source','Link','Project Funding Source',insert_after='custody_context_column'),f('custom_expected_return_date','Expected Return Date','Date',insert_after='custom_funding_source'),f('custom_return_against_movement','Return Against Movement','Link','Asset Movement',insert_after='custom_expected_return_date')])
 for dt in ('Employee Separation','Employee Offboarding'):
  add(out,dt,[f('custody_clearance_section','Custody Clearance','Section Break',insert_after='employee',collapsible=1),f('custom_custody_exception_approved','Custody Exception Approved','Check',insert_after='custody_clearance_section'),f('custom_custody_exception_reason','Custody Exception Reason','Small Text',insert_after='custom_custody_exception_approved')])

 # Acceptance and reinspection fields added without replacing standard ERPNext fields.
 add(out,'Purchase Receipt Item',[
  f('custom_rejected_qty','Rejected Quantity','Float',insert_after='custom_accepted_qty',default='0'),
 ])
 add(out,'Stock Entry',[
  f('custom_quality_inspection','Quality Inspection','Link','Quality Inspection',insert_after='custom_return_against_stock_entry',read_only=1),
 ])
 add(out,'Purchase Receipt',[
  f('custom_quality_inspection','Quality Inspection','Link','Quality Inspection',insert_after='custom_procurement_acceptance',read_only=1),
 ])
 add(out,'Stock Entry Detail',[
  f('custom_return_against_stock_entry_detail','Return Against Stock Entry Detail','Link','Stock Entry Detail',insert_after='material_request_item',depends_on='eval:parent.custom_return_against_stock_entry'),
 ])
 # Complete conditional behavior for issue requests without duplicating fields.
 for row in out.get('Material Request', []):
  if row.get('fieldname') == 'custom_issue_usage_type':
   row['mandatory_depends_on'] = 'eval:doc.material_request_type == "Material Issue"'
  elif row.get('fieldname') == 'custom_issue_purpose':
   row['mandatory_depends_on'] = 'eval:doc.material_request_type == "Material Issue" && doc.custom_issue_usage_type'
  elif row.get('fieldname') == 'custom_workplan_activity':
   row['depends_on'] = 'eval:["Project Activity","Beneficiary Distribution","Field Location"].includes(doc.custom_issue_usage_type)'
   row['mandatory_depends_on'] = 'eval:doc.custom_issue_usage_type == "Project Activity"'
  elif row.get('fieldname') == 'custom_delivery_location':
   row['depends_on'] = 'eval:["Project Activity","Beneficiary Distribution","Field Location","Partner Handover","Transfer","External Delivery","Emergency Issue"].includes(doc.custom_issue_usage_type)'
   row['mandatory_depends_on'] = 'eval:["Beneficiary Distribution","Field Location","Partner Handover","Transfer","External Delivery"].includes(doc.custom_issue_usage_type)'
  elif row.get('fieldname') == 'custom_recipient_type':
   row['mandatory_depends_on'] = 'eval:doc.material_request_type == "Material Issue"'
  elif row.get('fieldname') == 'custom_recipient_employee':
   row['depends_on'] = 'eval:doc.custom_recipient_type == "Employee"'
   row['mandatory_depends_on'] = 'eval:doc.custom_recipient_type == "Employee"'
  elif row.get('fieldname') == 'custom_required_delivery_date':
   row['depends_on'] = 'eval:["Project Activity","Beneficiary Distribution","Field Location","Partner Handover","Transfer","External Delivery"].includes(doc.custom_issue_usage_type)'
  elif row.get('fieldname') == 'custom_return_expected':
   row['depends_on'] = 'eval:["Employee Use","Temporary Issue"].includes(doc.custom_issue_usage_type)'
  elif row.get('fieldname') == 'custom_expected_return_date':
   row['depends_on'] = 'eval:doc.custom_return_expected == 1'
   row['mandatory_depends_on'] = 'eval:doc.custom_return_expected == 1'

 # Transport and arrival data on the standard Purchase Receipt.
 add(out,'Purchase Receipt',[
  f('delivery_transport_section','Delivery and Transport','Section Break',insert_after='supplier_delivery_note',collapsible=1),
  f('custom_delivery_method','Delivery Method','Select','Supplier Delivery\nOrganization Vehicle\nThird-Party Transporter\nRecipient Pickup\nCourier\nOther',insert_after='delivery_transport_section'),
  f('custom_transport_provider','Transport Provider','Data',insert_after='custom_delivery_method',depends_on='eval:["Third-Party Transporter","Courier","Other"].includes(doc.custom_delivery_method)',mandatory_depends_on='eval:["Third-Party Transporter","Courier"].includes(doc.custom_delivery_method)'),
  f('custom_driver_name','Driver or Courier Name','Data',insert_after='custom_transport_provider',depends_on='eval:doc.custom_delivery_method && doc.custom_delivery_method != "Recipient Pickup"'),
  f('custom_driver_phone','Driver or Courier Phone','Data','Phone',insert_after='custom_driver_name',depends_on='eval:doc.custom_delivery_method && doc.custom_delivery_method != "Recipient Pickup"'),
  f('delivery_transport_column','', 'Column Break',insert_after='custom_driver_phone'),
  f('custom_vehicle_type','Vehicle Type','Data',insert_after='delivery_transport_column',depends_on='eval:["Supplier Delivery","Organization Vehicle","Third-Party Transporter"].includes(doc.custom_delivery_method)'),
  f('custom_vehicle_number','Vehicle or Plate Number','Data',insert_after='custom_vehicle_type',depends_on='eval:["Supplier Delivery","Organization Vehicle","Third-Party Transporter"].includes(doc.custom_delivery_method)',mandatory_depends_on='eval:["Organization Vehicle","Third-Party Transporter"].includes(doc.custom_delivery_method)'),
  f('custom_waybill_number','Waybill or Dispatch Note','Data',insert_after='custom_vehicle_number',depends_on='eval:doc.custom_delivery_method && doc.custom_delivery_method != "Recipient Pickup"'),
  f('custom_arrival_datetime','Arrival Date and Time','Datetime',insert_after='custom_waybill_number',depends_on='eval:doc.custom_delivery_method'),
  f('custom_delivery_condition','Delivery Condition','Select','Good\nDamaged\nShort\nExcess\nMixed\nUnder Review',insert_after='custom_arrival_datetime',depends_on='eval:doc.custom_delivery_method'),
  f('custom_delivery_evidence','Delivery Evidence','Attach',insert_after='custom_delivery_condition',depends_on='eval:doc.custom_delivery_method'),
  f('custom_delivery_remarks','Delivery Remarks','Small Text',insert_after='custom_delivery_evidence',depends_on='eval:doc.custom_delivery_condition && doc.custom_delivery_condition != "Good"',mandatory_depends_on='eval:doc.custom_delivery_condition && doc.custom_delivery_condition != "Good"'),
 ])
 return out

def _migrate_and_remove_legacy_activity_references():
 for doctype in ('Material Request','Stock Entry'):
  legacy_name=f'{doctype}-custom_activity_reference'
  if not frappe.db.exists('Custom Field',legacy_name):
   continue
  if frappe.get_meta(doctype).has_field('custom_workplan_activity'):
   rows=frappe.get_all(doctype,filters={'custom_activity_reference':['is','set'],'custom_workplan_activity':['is','not set']},fields=['name','custom_activity_reference'])
   for row in rows:
    legacy=(row.custom_activity_reference or '').strip()
    if legacy and frappe.db.exists('Project Workplan Activity',legacy):
     frappe.db.set_value(doctype,row.name,'custom_workplan_activity',legacy,update_modified=False)
  frappe.delete_doc('Custom Field',legacy_name,ignore_permissions=True,force=True)
  frappe.clear_cache(doctype=doctype)

def provision_custom_fields():
 defs=definitions();create_custom_fields_if_changed(defs,update=True)
 _migrate_and_remove_legacy_activity_references()
 for dt in defs:frappe.clear_cache(doctype=dt)
