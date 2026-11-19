import frappe
from frappe import _
from frappe.utils import flt

@frappe.whitelist()
def get_company_defaults(company):
    if not company:return {}
    row=frappe.db.get_value("Company",company,["default_currency","custom_enable_shared_cost_allocation","custom_shared_cost_default_cost_center","custom_indirect_cost_expense_account","custom_indirect_cost_recovery_account","custom_payroll_account_group","custom_require_allocation_before_project_closeout","custom_allow_post_closeout_adjustment"],as_dict=True) or {}
    return row

@frappe.whitelist()
def get_target_defaults(project=None,budget_line=None,funding_agreement=None,company=None):
    result={"project":project,"budget_line":budget_line,"funding_agreement":funding_agreement}
    if project:
        p=frappe.db.get_value("Project",project,["company","cost_center","status"],as_dict=True) or {}
        if company and p.get("company")!=company:frappe.throw(_("Project {0} does not belong to Company {1}.").format(project,company))
        result.update({"project_company":p.get("company"),"cost_center":p.get("cost_center"),"project_status":p.get("status")})
    if budget_line:
        bl=frappe.db.get_value("Budget Line",budget_line,["project","funding_agreement","donor_currency","base_currency","eligibility_start_date","eligibility_end_date","line_cost","status","is_group"],as_dict=True) or {}
        if project and bl.get("project")!=project:frappe.throw(_("Budget Line does not belong to the selected Project."))
        if bl.get("is_group"):frappe.throw(_("A group Budget Line cannot receive an allocation."))
        result.update({"budget_line_project":bl.get("project"),"funding_agreement":funding_agreement or bl.get("funding_agreement"),"budget_line_status":bl.get("status"),"budget_amount":bl.get("line_cost"),"eligibility_start_date":bl.get("eligibility_start_date"),"eligibility_end_date":bl.get("eligibility_end_date")})
    agreement=result.get("funding_agreement")
    if agreement:
        fa=frappe.db.get_value("Funding Agreement",agreement,["project","company","donor","agreement_currency","indirect_cost_percent","eligibility_start_date","eligibility_end_date","status","exchange_rate","exchange_rate_date","exchange_rate_source"],as_dict=True) or {}
        if project and fa.get("project")!=project:frappe.throw(_("Funding Agreement does not belong to the selected Project."))
        if company and fa.get("company")!=company:frappe.throw(_("Funding Agreement does not belong to the selected Company."))
        result.update({"donor":fa.get("donor"),"donor_currency":fa.get("agreement_currency"),"indirect_rate_override":fa.get("indirect_cost_percent"),"eligibility_start_date":fa.get("eligibility_start_date") or result.get("eligibility_start_date"),"eligibility_end_date":fa.get("eligibility_end_date") or result.get("eligibility_end_date"),"agreement_status":fa.get("status"),"donor_exchange_rate":fa.get("exchange_rate"),"exchange_rate_date":fa.get("exchange_rate_date"),"exchange_rate_source":fa.get("exchange_rate_source")})
    return result

@frappe.whitelist()
def get_rule_defaults(rule):
    if not rule:return {}
    doc=frappe.get_doc("Shared Cost Allocation Rule",rule);doc.check_permission("read")
    return {"company":doc.company,"allocation_category":doc.allocation_category,"allocation_method":doc.allocation_method,"source_cost_center":doc.source_cost_center or frappe.get_cached_value("Company",doc.company,"custom_shared_cost_default_cost_center"),"period_start":doc.effective_from,"period_end":doc.effective_to,"posting_date":doc.effective_from,"currency":frappe.get_cached_value("Company",doc.company,"default_currency")}
