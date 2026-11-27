import frappe
from frappe import _
from frappe.utils import flt
from qorg.qorg.finance_period_control.actuals import actual_for_line
from qorg.qorg.finance_period_control.period_balances import period_balances

def execute(filters=None):
    f=frappe._dict(filters or {})
    if not f.company or not f.budget_period:return [],[],_("Select Company and Budget Period"),None,[]
    period=frappe.get_doc("Budget Period",f.budget_period)
    if period.company!=f.company:frappe.throw(_("Budget Period does not belong to Company"))
    conditions=["p.company=%s","pa.budget_period=%s"];values=[f.company,period.name]
    if f.project:conditions.append("bl.project=%s");values.append(f.project)
    if f.budget_line:conditions.append("bl.name=%s");values.append(f.budget_line)
    lines=frappe.db.sql("select bl.name budget_line,bl.name1 budget_line_name,bl.project,bl.parent_budget_line,bl.is_group,bl.lft,sum(pa.allocated_amount) budget,bl.recognition_basis from `tabBudget Line` bl inner join `tabProject` p on p.name=bl.project inner join `tabBudget Period Allocation` pa on pa.parent=bl.name where "+" and ".join(conditions)+" group by bl.name order by bl.project,bl.lft",tuple(values),as_dict=True)
    names=[x.budget_line for x in lines];commitments={x.budget_line:flt(x.amount) for x in period_balances(f.company,period.name,names,f.project)} if names else {}
    rows=[]
    for line in lines:
        actual=0 if line.is_group else actual_for_line(f.company,line.budget_line,period.from_date,period.to_date,line.recognition_basis)
        commitment=0 if line.is_group else commitments.get(line.budget_line,0);budget=flt(line.budget);used=actual+commitment;available=budget-used;utilization=used/budget*100 if budget else 0
        status="Over Budget" if available < -0.005 else "Warning" if utilization>=90 else "Healthy" if budget else "Review Required"
        rows.append({**line,"actual":actual,"commitment":commitment,"available":available,"utilization":utilization,"status":status,"currency":frappe.get_cached_value("Company",f.company,"default_currency")})
    columns=[{"label":_("Budget Line"),"fieldname":"budget_line","fieldtype":"Link","options":"Budget Line","width":260,"sticky":True},{"label":_("Project"),"fieldname":"project","fieldtype":"Link","options":"Project","width":180,"sticky":True},{"label":_("Budget"),"fieldname":"budget","fieldtype":"Currency","options":"currency","width":120},{"label":_("Actual"),"fieldname":"actual","fieldtype":"Currency","options":"currency","width":120},{"label":_("Commitment"),"fieldname":"commitment","fieldtype":"Currency","options":"currency","width":120},{"label":_("Available"),"fieldname":"available","fieldtype":"Currency","options":"currency","width":120},{"label":_("Utilization %"),"fieldname":"utilization","fieldtype":"Percent","width":110},{"label":_("Status"),"fieldname":"status","width":130}]
    leaves=[x for x in rows if not x.is_group]
    chart={"data":{"labels":[x.budget_line_name or x.budget_line for x in leaves[:20]],"datasets":[{"name":_("Budget"),"values":[flt(x.budget) for x in leaves[:20]]},{"name":_("Actual + Commitment"),"values":[flt(x.actual)+flt(x.commitment) for x in leaves[:20]]}]},"type":"bar"}
    summary=[{"value":sum(flt(x.budget) for x in leaves),"label":_("Period Budget"),"datatype":"Currency"},{"value":sum(flt(x.actual) for x in leaves),"label":_("Actual"),"datatype":"Currency"},{"value":sum(flt(x.commitment) for x in leaves),"label":_("Open Commitments"),"datatype":"Currency"},{"value":sum(flt(x.available) for x in leaves),"label":_("Available"),"datatype":"Currency"},{"value":sum(1 for x in leaves if x.status=="Over Budget"),"label":_("Over Budget"),"datatype":"Int","indicator":"Red"}]
    return columns,rows,None,chart,summary
