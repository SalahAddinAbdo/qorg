import frappe
from frappe import _

PROCESS_STAGES={
 "Procurement Notice":{"field":"procurement_process","states":["Setup Approved","Published or Invited"]},
 "Procurement Bid Opening":{"field":"procurement_process","states":["Submission Closed","Opening Completed"]},
 "Bid Precheck":{"field":"procurement_process","states":["Opening Completed"]},
 "Technical Evaluation":{"field":"procurement_process","states":["Opening Completed","Technical Evaluation Approved"]},
 "Financial Evaluation":{"field":"procurement_process","states":["Technical Evaluation Approved","Financial Evaluation Approved"]},
 "Evaluation Summary":{"field":"procurement_process","states":["Financial Evaluation Approved","Combined Evaluation Completed"]},
 "Award Recommendation":{"field":"procurement_process","states":["Combined Evaluation Completed"]},
 "Award Decision":{"field":"procurement_process","states":["Combined Evaluation Completed","Award Approved"]},
 "Procurement Contract":{"field":"procurement_process","states":["Award Approved","Closed"]},
}

def _submitted_mr(name):
 doc=frappe.get_doc("Material Request",name);doc.check_permission("read")
 if doc.docstatus!=1 or doc.material_request_type!="Purchase":frappe.throw(_("A submitted Purchase Material Request is required."))
 doc.run_method("validate");return doc

@frappe.whitelist()
def get_procurement_action_state(material_request):
 doc=_submitted_mr(material_request);existing=frappe.db.get_value("Procurement Process",{"material_request":doc.name,"docstatus":["<",2]},"name")
 return {"expected_action":doc.custom_procurement_next_action,"existing_procurement_process":existing,"policy_rule":doc.custom_procurement_policy_rule,"procurement_method":doc.custom_procurement_method,"estimated_value":doc.custom_estimated_procurement_value}

@frappe.whitelist()
def create_or_open_procurement_process(material_request):
 doc=_submitted_mr(material_request)
 if doc.custom_procurement_next_action!="Create Procurement Process":frappe.throw(_("The applied procurement policy does not permit a Procurement Process."))
 existing=frappe.db.get_value("Procurement Process",{"material_request":doc.name,"docstatus":["<",2]},"name")
 if existing:return existing
 if not frappe.has_permission("Procurement Process","create"):frappe.throw(_("Not permitted to create Procurement Process."),frappe.PermissionError)
 process=frappe.get_doc({"doctype":"Procurement Process","material_request":doc.name,"company":doc.company,"project":doc.project,"currency":frappe.get_cached_value("Company",doc.company,"default_currency"),"estimated_value":doc.custom_estimated_procurement_value,"procurement_type":doc.custom_procurement_type,"policy_rule":doc.custom_procurement_policy_rule,"procurement_method":doc.custom_procurement_method,"title":doc.title or doc.name})
 process.insert();return process.name

@frappe.whitelist()
def create_or_open_process_stage(process_name,target_doctype,defaults=None):
 if target_doctype not in PROCESS_STAGES:frappe.throw(_("Unsupported procurement stage."))
 process=frappe.get_doc("Procurement Process",process_name);process.check_permission("read");spec=PROCESS_STAGES[target_doctype]
 if process.status not in spec["states"]:frappe.throw(_("{0} cannot be created while the process is in {1}.").format(target_doctype,process.status))
 if not frappe.has_permission(target_doctype,"create"):frappe.throw(_("Not permitted to create {0}.").format(target_doctype),frappe.PermissionError)
 values={"doctype":target_doctype,spec["field"]:process.name}
 if defaults:
  if isinstance(defaults,str):defaults=frappe.parse_json(defaults)
  values.update({k:v for k,v in defaults.items() if frappe.get_meta(target_doctype).has_field(k)})
 unique={spec["field"]:process.name,"docstatus":["<",2]}
 if values.get("submission"):unique["submission"]=values["submission"]
 existing=frappe.db.get_value(target_doctype,unique,"name")
 if existing:return existing
 doc=frappe.get_doc(values);doc.insert();return doc.name

@frappe.whitelist()
def create_or_open_contract(award_decision):
 award=frappe.get_doc("Award Decision",award_decision);award.check_permission("read")
 if award.decision!="Approved":frappe.throw(_("The award decision must be Approved before contract creation."))
 existing=frappe.db.get_value("Procurement Contract",{"award_decision":award.name,"docstatus":["<",2]},"name")
 if existing:return existing
 process=frappe.get_doc("Procurement Process",award.procurement_process)
 if process.status not in ("Award Approved","Closed"):frappe.throw(_("The procurement award must be approved."))
 doc=frappe.get_doc({"doctype":"Procurement Contract","award_decision":award.name,"procurement_process":process.name,"supplier":award.awarded_supplier,"contract_value":award.awarded_amount,"company":process.company,"project":process.project,"currency":process.currency,"contract_title":process.title})
 doc.insert();return doc.name

@frappe.whitelist()
def create_or_open_contract_record(contract_name,target_doctype):
 allowed={"Commitment Ledger":"procurement_process","Procure Acceptance":"procurement_process","Procurement Amendment":"procurement_process"}
 if target_doctype not in allowed:frappe.throw(_("Unsupported contract action."))
 contract=frappe.get_doc("Procurement Contract",contract_name);contract.check_permission("read")
 if not frappe.has_permission(target_doctype,"create"):frappe.throw(_("Not permitted to create {0}.").format(target_doctype),frappe.PermissionError)
 if contract.status not in ("Active","Under Approval"):frappe.throw(_("The contract must be active or under approval."))
 filters={allowed[target_doctype]:contract.procurement_process,"docstatus":["<",2]}
 if target_doctype=="Commitment Ledger":
  existing=frappe.db.get_value(target_doctype,filters,"name")
  if existing:return existing
 values={"doctype":target_doctype,"procurement_process":contract.procurement_process}
 meta=frappe.get_meta(target_doctype)
 for field,value in (("company",contract.company),("project",contract.project),("budget_line",contract.budget_line),("currency",contract.currency)):
  if meta.has_field(field):values[field]=value
 doc=frappe.get_doc(values);doc.insert();return doc.name

