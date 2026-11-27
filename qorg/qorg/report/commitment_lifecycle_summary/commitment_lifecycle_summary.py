import frappe
from frappe import _
from frappe.utils import flt
from qorg.qorg.finance_period_control.period_balances import COMMITMENT_STAGES

def execute(filters=None):
    f=frappe._dict(filters or {})
    if not f.company or not f.budget_period:return [],[],_("Select Company and Budget Period")
    cond=["cl.company=%s","ce.commitment_period=%s","ce.stage in %s","cl.docstatus<2"]
    vals=[f.company,f.budget_period,COMMITMENT_STAGES]
    if f.project:cond.append("ce.project=%s");vals.append(f.project)
    if f.budget_line:cond.append("ce.budget_line=%s");vals.append(f.budget_line)
    rows=frappe.db.sql("select cl.name ledger,ce.project,ce.budget_line,cl.currency,cl.lifecycle_status,sum(case when ce.stage='Requested' and ce.direction='Increase' then ce.base_amount when ce.stage='Requested' then -ce.base_amount else 0 end) requested,sum(case when ce.stage='Ordered' and ce.direction='Increase' then ce.base_amount when ce.stage='Ordered' then -ce.base_amount else 0 end) ordered,sum(case when ce.stage='Contracted' and ce.direction='Increase' then ce.base_amount when ce.stage='Contracted' then -ce.base_amount else 0 end) contracted,sum(case when ce.stage='Invoiced' and ce.direction='Increase' then ce.base_amount when ce.stage='Invoiced' then -ce.base_amount else 0 end) invoiced,sum(case when ce.direction='Increase' then ce.base_amount else -ce.base_amount end) open_commitment,cl.last_reference_doctype,cl.last_reference_name from `tabCommitment Entry` ce inner join `tabCommitment Ledger` cl on cl.name=ce.parent where "+" and ".join(cond)+" group by cl.name,ce.project,ce.budget_line having open_commitment>0.005 order by ce.project,ce.budget_line,cl.modified desc",tuple(vals),as_dict=True)
    cols=[{"label":_("Ledger"),"fieldname":"ledger","fieldtype":"Link","options":"Commitment Ledger","width":160,"sticky":True},{"label":_("Project"),"fieldname":"project","fieldtype":"Link","options":"Project","width":160,"sticky":True},{"label":_("Budget Line"),"fieldname":"budget_line","fieldtype":"Link","options":"Budget Line","width":230},{"label":_("Status"),"fieldname":"lifecycle_status","width":120},{"label":_("Requested"),"fieldname":"requested","fieldtype":"Currency","options":"currency","width":110},{"label":_("Ordered"),"fieldname":"ordered","fieldtype":"Currency","options":"currency","width":110},{"label":_("Contracted"),"fieldname":"contracted","fieldtype":"Currency","options":"currency","width":110},{"label":_("Invoiced"),"fieldname":"invoiced","fieldtype":"Currency","options":"currency","width":110},{"label":_("Open"),"fieldname":"open_commitment","fieldtype":"Currency","options":"currency","width":110},{"label":_("Reference"),"fieldname":"last_reference_name","fieldtype":"Dynamic Link","options":"last_reference_doctype","width":160},{"fieldname":"currency","fieldtype":"Link","options":"Currency","hidden":1}]
    summary=[{"value":sum(flt(r.open_commitment) for r in rows),"label":_("Open Commitments"),"datatype":"Currency"},{"value":len(rows),"label":_("Active Period Ledgers"),"datatype":"Int"}]
    return cols,rows,None,None,summary
