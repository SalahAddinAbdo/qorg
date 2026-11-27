import frappe
from frappe import _
from frappe.utils import flt
from qorg.qorg.finance_period_control.period_balances import COMMITMENT_STAGES

def execute(filters=None):
    f=frappe._dict(filters or {});conditions=["cl.company=%s"];values=[f.company]
    if f.project:conditions.append("cl.project=%s");values.append(f.project)
    rows=frappe.db.sql("select cl.name ledger,cl.project,cl.budget_line,cl.open_commitment,cl.lifecycle_status,sum(case when ce.stage in %s and ce.direction='Increase' then coalesce(ce.base_amount,ce.amount,0) when ce.stage in %s and ce.direction='Decrease' then -coalesce(ce.base_amount,ce.amount,0) else 0 end) calculated_open,sum(case when coalesce(ce.event_key,'')='' then 1 else 0 end) missing_keys,sum(case when ce.stage='Invoiced' and ce.direction='Increase' and ce.matching_status in ('Pending GL','Partially Matched','Exception') then 1 else 0 end) pending_gl from `tabCommitment Ledger` cl left join `tabCommitment Entry` ce on ce.parent=cl.name where "+" and ".join(conditions)+" group by cl.name having abs(coalesce(cl.open_commitment,0)-coalesce(calculated_open,0))>0.01 or missing_keys>0 or pending_gl>0",tuple([COMMITMENT_STAGES,COMMITMENT_STAGES]+values),as_dict=True)
    for row in rows:row.variance=flt(row.open_commitment)-flt(row.calculated_open)
    columns=[{"label":_("Ledger"),"fieldname":"ledger","fieldtype":"Link","options":"Commitment Ledger","width":180,"sticky":True},{"label":_("Project"),"fieldname":"project","fieldtype":"Link","options":"Project","width":160,"sticky":True},{"label":_("Budget Line"),"fieldname":"budget_line","fieldtype":"Link","options":"Budget Line","width":240},{"label":_("Stored Open"),"fieldname":"open_commitment","fieldtype":"Currency","width":120},{"label":_("Calculated Open"),"fieldname":"calculated_open","fieldtype":"Currency","width":130},{"label":_("Variance"),"fieldname":"variance","fieldtype":"Currency","width":110},{"label":_("Missing Keys"),"fieldname":"missing_keys","fieldtype":"Int","width":110},{"label":_("Pending GL"),"fieldname":"pending_gl","fieldtype":"Int","width":100}]
    return columns,rows
