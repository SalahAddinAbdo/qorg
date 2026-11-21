import frappe
from frappe import _
from .funding_plan import get_effective_plan
from .component_policy import effective_policy

def _issue(code,severity,message,reference_type=None,reference=None): return {"code":code,"severity":severity,"message":message,"reference_type":reference_type,"reference":reference}
def evaluate_payroll_entry(payroll_entry):
    pe=frappe.get_doc("Payroll Entry",payroll_entry);issues=[]
    if pe.docstatus!=1: issues.append(_issue("PAYROLL_NOT_SUBMITTED","Blocker",_("Payroll Entry must be submitted."),"Payroll Entry",pe.name))
    slips=frappe.get_all("Salary Slip",filters={"payroll_entry":pe.name,"docstatus":1},fields=["name","employee","currency"],limit_page_length=0)
    if not slips: issues.append(_issue("NO_SUBMITTED_SLIPS","Blocker",_("No submitted Salary Slips were found."),"Payroll Entry",pe.name))
    company_currency=frappe.db.get_value("Company",pe.company,"default_currency")
    if not company_currency: issues.append(_issue("MISSING_COMPANY_CURRENCY","Blocker",_("Company default currency is missing."),"Company",pe.company))
    company=frappe.get_doc("Company",pe.company)
    if not company.get("custom_payroll_allocation_clearing_account"): issues.append(_issue("MISSING_CLEARING_ACCOUNT","Warning",_("Payroll allocation clearing account is missing."),"Company",pe.company))
    for slip in slips:
        try:plan=get_effective_plan(slip.employee,pe.end_date)
        except Exception as e:plan=None;issues.append(_issue("PLAN_CONFLICT","Blocker",str(e),"Employee",slip.employee))
        if not plan: issues.append(_issue("MISSING_FUNDING_PLAN","Blocker",_("No active Workforce Funding Plan for employee {0}.").format(slip.employee),"Employee",slip.employee));continue
        if plan.allocation_method=="Approved Timesheet" and not frappe.db.exists("Timesheet",{"employee":slip.employee,"docstatus":1,"start_date":["<=",pe.end_date],"end_date":[">=",pe.start_date]}): issues.append(_issue("MISSING_TIMESHEET","Blocker",_("Submitted Timesheet is required for employee {0}.").format(slip.employee),"Employee",slip.employee))
        if plan.allocation_method=="Monthly Certified Effort" and not frappe.db.exists("Monthly Effort Certification",{"employee":slip.employee,"docstatus":1,"status":"Locked","start_date":["<=",pe.end_date],"end_date":[">=",pe.start_date]}): issues.append(_issue("MISSING_CERTIFIED_EFFORT","Blocker",_("Locked Monthly Effort Certification is required for employee {0}.").format(slip.employee),"Employee",slip.employee))
        policy=effective_policy(pe.company,pe.end_date,None,None)
        if not policy: issues.append(_issue("MISSING_COST_POLICY","Blocker",_("No effective Payroll Cost Policy was found."),"Company",pe.company))
    status="Blocked" if any(x["severity"]=="Blocker" for x in issues) else ("Warnings" if issues else "Passed")
    if pe.meta.has_field("custom_payroll_preflight_status"): frappe.db.set_value("Payroll Entry",pe.name,"custom_payroll_preflight_status",status,update_modified=False)
    return {"payroll_entry":pe.name,"status":status,"company_currency":company_currency,"salary_slip_count":len(slips),"issues":issues}
