import frappe
from frappe.utils import flt

COMMITMENT_STAGES=("Requested","Reserved","Ordered","Contracted","Invoiced")

def open_commitment_for_period(budget_line, period, company=None):
    conditions=["ce.budget_line=%s","ce.commitment_period=%s","ce.stage in %s","cl.docstatus<2"]
    values=[budget_line,period,COMMITMENT_STAGES]
    if company:
        conditions.append("cl.company=%s");values.append(company)
    amount=frappe.db.sql("select coalesce(sum(case when ce.direction='Increase' then ce.base_amount else -ce.base_amount end),0) from `tabCommitment Entry` ce inner join `tabCommitment Ledger` cl on cl.name=ce.parent where "+" and ".join(conditions),tuple(values))[0][0]
    return max(flt(amount),0)

def period_balances(company,period,budget_lines=None,project=None):
    conditions=["cl.company=%s","ce.commitment_period=%s","ce.stage in %s","cl.docstatus<2"]
    values=[company,period,COMMITMENT_STAGES]
    if budget_lines:
        conditions.append("ce.budget_line in %s");values.append(tuple(budget_lines))
    if project:
        conditions.append("ce.project=%s");values.append(project)
    rows=frappe.db.sql("select ce.budget_line,ce.project,sum(case when ce.direction='Increase' then ce.base_amount else -ce.base_amount end) amount from `tabCommitment Entry` ce inner join `tabCommitment Ledger` cl on cl.name=ce.parent where "+" and ".join(conditions)+" group by ce.budget_line,ce.project",tuple(values),as_dict=True)
    return [r for r in rows if flt(r.amount)>0.005]
