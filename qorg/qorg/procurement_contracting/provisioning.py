import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
ROLES=['Procurement Officer','Procurement Manager','Bid Opening Committee Member','Technical Evaluation Committee Member','Financial Evaluation Committee Member','Main Committee Member','Procurement Award Approver','Budget Controller','Contract Manager']
METHODS=[('Direct Purchase','Direct',0,0,1),('Request for Quotations','RFQ',0,1,0),('Restricted Tender','Restricted',1,0,0),('Open Tender','Open',1,0,0),('Request for Proposals','RFP',1,0,0),('Single Source','Single Source',1,0,0),('Emergency Procurement','Emergency',1,0,0),('Framework Call-off','Framework',0,0,1)]
def provision_procurement_contracting():
 for role in ROLES:
  if not frappe.db.exists('Role',role): frappe.get_doc({'doctype':'Role','role_name':role,'desk_access':1}).insert(ignore_permissions=True)
 create_custom_fields({'Material Request':[{'fieldname':'qorg_procurement_section','label':'Procurement Policy','fieldtype':'Section Break','insert_after':'schedule_date'},{'fieldname':'custom_procurement_type','label':'Procurement Type','fieldtype':'Select','options':'Goods\nServices\nWorks\nConsultancy\nMixed','insert_after':'qorg_procurement_section'},{'fieldname':'custom_estimated_procurement_value','label':'Estimated Procurement Value','fieldtype':'Currency','read_only':1,'insert_after':'custom_procurement_type'},{'fieldname':'custom_procurement_policy_rule','label':'Procurement Policy Rule','fieldtype':'Link','options':'Procurement Policy Rule','read_only':1,'insert_after':'custom_estimated_procurement_value'},{'fieldname':'custom_procurement_method','label':'Procurement Method','fieldtype':'Link','options':'Procurement Method','read_only':1,'insert_after':'custom_procurement_policy_rule'},{'fieldname':'custom_procurement_next_action','label':'Next Procurement Action','fieldtype':'Data','read_only':1,'insert_after':'custom_procurement_method'},{'fieldname':'custom_requires_procurement_process','label':'Requires Procurement Process','fieldtype':'Check','read_only':1,'insert_after':'custom_procurement_next_action'},{'fieldname':'custom_procurement_process','label':'Procurement Process','fieldtype':'Link','options':'Procurement Process','read_only':1,'insert_after':'custom_requires_procurement_process'},
       {'fieldname':'custom_minimum_quotations','label':'Minimum Quotations','fieldtype':'Int','read_only':1,'insert_after':'custom_procurement_process'},
       {'fieldname':'custom_requires_public_notice','label':'Requires Public Notice','fieldtype':'Check','read_only':1,'insert_after':'custom_minimum_quotations'},
       {'fieldname':'custom_requires_opening_committee','label':'Requires Opening Committee','fieldtype':'Check','read_only':1,'insert_after':'custom_requires_public_notice'},
       {'fieldname':'custom_requires_technical_evaluation','label':'Requires Technical Evaluation','fieldtype':'Check','read_only':1,'insert_after':'custom_requires_opening_committee'},
       {'fieldname':'custom_requires_financial_evaluation','label':'Requires Financial Evaluation','fieldtype':'Check','read_only':1,'insert_after':'custom_requires_technical_evaluation'},
       {'fieldname':'custom_requires_two_envelope','label':'Requires Two Envelope','fieldtype':'Check','read_only':1,'insert_after':'custom_requires_financial_evaluation'},
       {'fieldname':'custom_technical_weight','label':'Technical Weight %','fieldtype':'Percent','read_only':1,'insert_after':'custom_requires_two_envelope'},
       {'fieldname':'custom_financial_weight','label':'Financial Weight %','fieldtype':'Percent','read_only':1,'insert_after':'custom_technical_weight'},
       {'fieldname':'custom_technical_threshold','label':'Technical Threshold %','fieldtype':'Percent','read_only':1,'insert_after':'custom_financial_weight'},
       {'fieldname':'custom_requires_contract','label':'Requires Contract','fieldtype':'Check','read_only':1,'insert_after':'custom_technical_threshold'},
       {'fieldname':'custom_procurement_exception_reason','label':'Procurement Exception Reason','fieldtype':'Small Text','insert_after':'custom_requires_contract'},
       {'fieldname':'custom_procurement_policy_snapshot','label':'Procurement Policy Snapshot','fieldtype':'Long Text','read_only':1,'hidden':1,'insert_after':'custom_procurement_exception_reason'}],'Material Request Item':[{'fieldname':'custom_estimated_unit_cost','label':'Estimated Unit Cost','fieldtype':'Currency','insert_after':'rate'},
       {'fieldname':'custom_estimated_amount','label':'Estimated Amount','fieldtype':'Currency','read_only':1,'insert_after':'custom_estimated_unit_cost'},
       {'fieldname':'custom_estimate_currency','label':'Estimate Currency','fieldtype':'Link','options':'Currency','insert_after':'custom_estimated_amount'},
       {'fieldname':'custom_estimate_source','label':'Estimate Source','fieldtype':'Select','options':'Market Survey\nPrevious Purchase\nSupplier Budgetary Quote\nFramework Agreement\nCatalogue\nProfessional Estimate\nOther','insert_after':'custom_estimate_currency'},
       {'fieldname':'custom_estimate_reference','label':'Estimate Reference','fieldtype':'Data','insert_after':'custom_estimate_source'},
       {'fieldname':'custom_non_stock_procurement_type','label':'Non-stock Procurement Type','fieldtype':'Select','options':'Goods\nServices\nWorks\nConsultancy','insert_after':'custom_estimate_reference'},
       {'fieldname':'custom_required_specification','label':'Required Specification or Scope','fieldtype':'Small Text','insert_after':'custom_non_stock_procurement_type'},
       {'fieldname':'custom_required_delivery_location','label':'Required Delivery Location','fieldtype':'Data','insert_after':'custom_required_specification'},
       {'fieldname':'custom_required_delivery_date','label':'Required Delivery Date','fieldtype':'Date','insert_after':'custom_required_delivery_location'}]},update=True)
 for name,mode,process,rfq,direct in METHODS:
  if not frappe.db.exists('Procurement Method',{'method_name':name}): frappe.get_doc({'doctype':'Procurement Method','naming_series':'PRM-.YYYY.-.#####','method_name':name,'procurement_mode':mode,'requires_procurement_process':process,'uses_standard_rfq':rfq,'allows_direct_purchase_order':direct}).insert(ignore_permissions=True)

WORKFLOW_STATES=["Draft Setup","Setup Approved","Published or Invited","Submission Closed","Opening Completed","Technical Evaluation In Progress","Technical Evaluation Approved","Financial Evaluation In Progress","Financial Evaluation Approved","Combined Evaluation Completed","Recommendation Submitted","Award Approved","Closed"]
def _provision_workflow_states():
 for state in WORKFLOW_STATES:
  if not frappe.db.exists("Workflow State",state): frappe.get_doc({"doctype":"Workflow State","workflow_state_name":state,"style":"Primary"}).insert(ignore_permissions=True)

def provision_procurement_contracting_full():
 provision_procurement_contracting(); _provision_workflow_states()

def _provision_budget_line_dimension():
 if not frappe.db.exists("DocType","Accounting Dimension") or not frappe.db.exists("DocType","Budget Line"): return
 meta=frappe.get_meta("Accounting Dimension")
 reference_field=next((f.fieldname for f in meta.fields if f.fieldname in ("document_type","reference_document_type")),None)
 if not reference_field: return
 if frappe.db.exists("Accounting Dimension",{reference_field:"Budget Line"}): return
 values={"doctype":"Accounting Dimension",reference_field:"Budget Line"}
 for field,value in (("label","Budget Line"),("fieldname","budget_line"),("disabled",0)):
  if meta.has_field(field): values[field]=value
 frappe.get_doc(values).insert(ignore_permissions=True)

def provision_procurement_contracting_full():
 provision_procurement_contracting(); _provision_workflow_states(); _provision_budget_line_dimension()

def provision_procurement_contracting_v13():
    provision_procurement_contracting_full()
    from qorg.qorg.procurement_contracting.notifications import provision_email_templates
    provision_email_templates()
def provision_procurement_contracting_v13_final():
    provision_procurement_contracting_v13()
    from qorg.qorg.procurement_contracting.notifications import provision_notifications
    from qorg.qorg.procurement_contracting.workflows import provision_workflows
    from qorg.qorg.procurement_contracting.print_formats import provision_print_formats
    provision_notifications(); provision_workflows(); provision_print_formats()
