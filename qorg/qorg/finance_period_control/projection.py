import frappe
from frappe.utils import flt, now_datetime, getdate
from qorg.qorg.finance_period_control.service import resolve_budget_period

def _period_allocation(line, period):
    return sum(flt(r.allocated_amount) for r in (line.get("period_allocations") or []) if r.budget_period==period)

def _actual(line, period_doc):
    from qorg.qorg.finance_period_control.actuals import actual_for_line
    return actual_for_line(period_doc.company,line.name,period_doc.from_date,period_doc.to_date,line.get("recognition_basis"))

def _commitment(line, period):
    from qorg.qorg.finance_period_control.period_balances import open_commitment_for_period
    company=line.project and frappe.db.get_value("Project",line.project,"company")
    return open_commitment_for_period(line.name,period,company)

def calculate_budget_line_projection(budget_line, posting_date=None, budget_period=None, persist=False):
    line=frappe.get_doc("Budget Line",budget_line) if isinstance(budget_line,str) else budget_line
    company=line.project and frappe.db.get_value("Project",line.project,"company")
    if not company: frappe.throw("Budget Line Project must have a Company")
    period,source=resolve_budget_period(company,posting_date or frappe.utils.today(),line.project,budget_period,False,"Budget Line","Allocation")
    budget=_period_allocation(line,period.name);actual=_actual(line,period);commitment=_commitment(line,period.name)
    available=budget-actual-commitment;utilization=((actual+commitment)/budget*100) if budget else 0
    if not budget:status="Review Required"
    elif available<0:status="Over Budget"
    elif utilization>=90:status="Warning"
    else:status="Healthy"
    result={"budget_line":line.name,"budget_period":period.name,"period_source":source,"budget":budget,"actual":actual,"commitment":commitment,"available":available,"utilization":utilization,"status":status,"as_of":now_datetime()}
    if persist:
        frappe.db.set_value("Budget Line",line.name,{"projected_budget_period":period.name,"projected_budget":budget,"projected_actual":actual,"projected_commitment":commitment,"projected_available":available,"projected_utilization":utilization,"projection_status":status,"projection_as_of":result["as_of"]},update_modified=False)
    return result

@frappe.whitelist()
def get_projection(budget_line,posting_date=None,budget_period=None):
    frappe.has_permission("Budget Line","read",doc=budget_line,throw=True)
    return calculate_budget_line_projection(budget_line,posting_date,budget_period,False)

@frappe.whitelist()
def refresh_projection(budget_line,posting_date=None,budget_period=None):
    frappe.has_permission("Budget Line","write",doc=budget_line,throw=True)
    return calculate_budget_line_projection(budget_line,posting_date,budget_period,True)

def refresh_for_ledger(doc,method=None):
    if doc.budget_line and doc.budget_period and not frappe.flags.in_migrate:
        calculate_budget_line_projection(doc.budget_line,budget_period=doc.budget_period,persist=True)
