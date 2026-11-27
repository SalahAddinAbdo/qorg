import frappe
from frappe.utils import flt,now_datetime
from qorg.qorg.finance_period_control.service import resolve_budget_period,get_control_policy
from qorg.qorg.finance_period_control.source_reconciliation import COMMITMENT_STAGES,EPSILON

def resolve_event_period(company,date,project,transaction_type,require_open=False):
    if get_control_policy(company,project)=="Disabled":return None
    period=resolve_budget_period(company,date,project,require_open=require_open,transaction_type=transaction_type)[0]
    from qorg.qorg.finance_period_control.policy_v2 import check_period_flags
    check_period_flags(period,transaction_type);return period.name

def stamp_commitment_event(event,doc,project=None):
    event.commitment_period=resolve_event_period(doc.company,doc.get("posting_date") or doc.get("transaction_date") or frappe.utils.today(),project or event.project,"Commitment",False);event.origin_period=event.commitment_period;event.control_policy=get_control_policy(doc.company,project or event.project);return event

def stamp_actual_event(event,company,date,project):event.actual_period=resolve_event_period(company,date,project,"Actual",False);return event

def net_open(period,company):
    rows=frappe.db.sql("select ce.parent,ce.event_key,ce.stage,ce.base_amount,ce.direction,ce.budget_line,ce.project,ce.company_currency,ce.origin_period,ce.source_row from `tabCommitment Entry` ce inner join `tabCommitment Ledger` cl on cl.name=ce.parent where cl.company=%s and cl.docstatus<2 and ce.commitment_period=%s and ce.stage in %s",(company,period,COMMITMENT_STAGES),as_dict=True)
    return rows,sum((flt(r.base_amount) if r.direction=="Increase" else -flt(r.base_amount)) for r in rows)

def _batch(source):return f"CFB|{source.name}|{frappe.generate_hash(length=12)}"
def carry_forward(source,target,batch):
    ledgers=frappe.get_all("Commitment Ledger",filters={"company":source.company,"docstatus":["<",2]},pluck="name")
    for name in ledgers:
        ledger=frappe.get_doc("Commitment Ledger",name)
        originals=[x for x in ledger.entries if x.commitment_period==source.name and x.stage in COMMITMENT_STAGES and x.direction=="Increase"]
        for original in originals:
            reversed_amount=sum(flt(x.base_amount or x.amount) for x in ledger.entries if x.reverses_event_key==original.event_key and x.commitment_period==source.name)
            amount=max(flt(original.base_amount or original.amount)-reversed_amount,0)
            if amount<=EPSILON:continue
            key=f"{batch}|{original.event_key}"
            if any(x.carry_forward_key==key for x in ledger.entries):continue
            common={"stage":original.stage,"source_row":original.source_row,"amount":amount,"base_amount":amount,"company_currency":original.company_currency,"budget_line":original.budget_line,"project":original.project,"origin_period":original.origin_period or source.name,"carry_forward_key":key,"carry_forward_batch":batch}
            ledger.append("entries",dict(common,posting_date=source.to_date,reference_doctype="Budget Period",reference_name=source.name,event_key=key+"|OUT",direction="Decrease",reverses_event_key=original.event_key,commitment_effect="Decrease Open Commitment",commitment_period=source.name,remarks=f"Carry forward out to {target.name}"))
            ledger.append("entries",dict(common,posting_date=target.from_date,reference_doctype="Budget Period",reference_name=target.name,event_key=key+"|IN",direction="Increase",commitment_effect="Increase Open Commitment",commitment_period=target.name,carry_forward_from=source.name,remarks=f"Carry forward in from {source.name}"))
        ledger.save(ignore_permissions=True)

def close_period(period_name,carry_forward_to=None):
    period=frappe.get_doc("Budget Period",period_name);period.check_permission("write")
    if period.status!="Open":frappe.throw("Only an Open Budget Period can be closed")
    rows,total=net_open(period.name,period.company);target=carry_forward_to or period.carry_forward_to;batch=None
    if total>EPSILON:
        if not target:frappe.throw("Net open commitments exist; select Carry Forward To")
        target_doc=frappe.get_doc("Budget Period",target)
        if target_doc.company!=period.company or target_doc.status!="Open" or target_doc.from_date<=period.to_date:frappe.throw("Carry-forward target must be a later Open period of the same Company")
        batch=_batch(period);carry_forward(period,target_doc,batch)
    period.status="Closed";period.closed_on=now_datetime();period.closed_by=frappe.session.user;period.last_carry_forward_batch=batch;period.last_carry_forward_reversed=0;period.save();return {"period":period.name,"status":"Closed","net_open":total,"batch":batch}

def reopen_period(period_name):
    period=frappe.get_doc("Budget Period",period_name);period.check_permission("write")
    if period.status!="Closed":frappe.throw("Only a Closed period can be reopened")
    batch=period.last_carry_forward_batch
    if batch and not period.last_carry_forward_reversed:
        for name in frappe.get_all("Commitment Ledger",filters={"entries.carry_forward_batch":batch},pluck="name",distinct=True):
            ledger=frappe.get_doc("Commitment Ledger",name)
            for original in [x for x in list(ledger.entries) if x.carry_forward_batch==batch]:
                key=f"REV|{original.event_key}"
                if any(x.event_key==key for x in ledger.entries):continue
                ledger.append("entries",{"stage":original.stage,"posting_date":frappe.utils.today(),"reference_doctype":"Budget Period","reference_name":period.name,"source_row":original.source_row,"event_key":key,"amount":original.base_amount,"base_amount":original.base_amount,"company_currency":original.company_currency,"direction":"Decrease" if original.direction=="Increase" else "Increase","budget_line":original.budget_line,"project":original.project,"reverses_event_key":original.event_key,"commitment_effect":"Decrease Open Commitment" if original.direction=="Increase" else "Increase Open Commitment","commitment_period":original.commitment_period,"origin_period":original.origin_period,"carry_forward_batch":batch,"remarks":"Controlled reversal on period reopen"})
            ledger.save(ignore_permissions=True)
        period.last_carry_forward_reversed=1
    period.status="Open";period.reopened_on=now_datetime();period.reopened_by=frappe.session.user;period.save();return {"period":period.name,"status":"Open","reversed_batch":batch}
@frappe.whitelist()
def close_budget_period(period,carry_forward_to=None):return close_period(period,carry_forward_to)
@frappe.whitelist()
def reopen_budget_period(period):return reopen_period(period)
