"""Globally consumptive GL matching. One GL amount can never be matched twice."""
import frappe
from frappe.utils import flt
from qorg.qorg.finance_period_control.actuals import account_clause
from qorg.qorg.finance_period_control.source_reconciliation import EPSILON,event_key

def _field(meta,name):return meta.has_field(name)
def _gl_rows(doc):
    meta=frappe.get_meta("GL Entry"); optional=[x for x in ("voucher_detail_no","budget_line","project","funding_agreement","donor") if _field(meta,x)]
    cols=",".join("gl.`%s`"%x for x in optional)
    return frappe.db.sql("select gl.name,gl.posting_date,gl.debit,gl.credit,gl.account"+(","+cols if cols else "")+" from `tabGL Entry` gl where gl.docstatus=1 and gl.is_cancelled=0 and gl.company=%s and gl.voucher_type='Purchase Invoice' and gl.voucher_no=%s order by gl.posting_date,gl.creation,gl.name",(doc.company,doc.name),as_dict=True)
def _consumed(gl_name):
    return flt(frappe.db.sql("select coalesce(sum(matched_base_amount),0) from `tabCommitment Entry` where gl_entry=%s and direction='Decrease'",gl_name)[0][0])
def _eligible(gl,event):
    basis=frappe.db.get_value("Budget Line",event.budget_line,"recognition_basis") or "Expense Only";acc=frappe.db.get_value("Account",gl.account,["root_type","account_type"],as_dict=True)
    if basis=="Expense Only" and acc.root_type!="Expense":return False
    if basis=="Asset Acquisition" and (acc.root_type!="Asset" or acc.account_type in ("Bank","Cash","Receivable","Accumulated Depreciation")):return False
    if basis=="Expense and Asset Acquisition" and not (acc.root_type=="Expense" and acc.account_type!="Depreciation" or acc.root_type=="Asset" and acc.account_type not in ("Bank","Cash","Receivable","Accumulated Depreciation")):return False
    for field in ("budget_line","project","funding_agreement","donor"):
        if gl.get(field) and event.get(field) and gl.get(field)!=event.get(field):return False
    if gl.get("voucher_detail_no") and gl.voucher_detail_no!=event.source_row:return False
    return True

def reconcile(doc,method=None):
    gls=_gl_rows(doc);available={g.name:max(flt(g.debit)-flt(g.credit)-_consumed(g.name),0) for g in gls}
    ledgers=frappe.get_all("Commitment Ledger",filters={"company":doc.company,"entries.reference_doctype":"Purchase Invoice","entries.reference_name":doc.name},pluck="name",distinct=True)
    for name in ledgers:
        ledger=frappe.get_doc("Commitment Ledger",name)
        events=[e for e in ledger.entries if e.reference_doctype=="Purchase Invoice" and e.reference_name==doc.name and e.stage=="Invoiced" and e.direction=="Increase"]
        for original in events:
            used=sum(flt(x.matched_base_amount or x.base_amount) for x in ledger.entries if x.reverses_event_key==original.event_key and x.reference_doctype=="GL Entry")
            need=max(flt(original.base_amount)-used,0)
            for gl in gls:
                if need<=EPSILON:break
                if available[gl.name]<=EPSILON or not _eligible(gl,original):continue
                take=min(need,available[gl.name]);key=f"GLMATCH|{gl.name}|{original.event_key}|{original.cost_distribution_row or 'BASE'}|{take:.6f}"
                if frappe.db.exists("Commitment Entry",{"matching_key":key}):available[gl.name]-=take;need-=take;continue
                ev=ledger.append("entries",{"stage":"Invoiced","posting_date":gl.posting_date,"reference_doctype":"GL Entry","reference_name":gl.name,"source_row":gl.name,"event_key":event_key("GL Entry",gl.name,original.source_row,"Invoiced","Decrease"),"amount":take,"base_amount":take,"matched_base_amount":take,"company_currency":original.company_currency,"direction":"Decrease","budget_line":original.budget_line,"project":original.project,"funding_agreement":original.funding_agreement,"donor":original.donor,"cost_distribution_row":original.cost_distribution_row,"source_parent_doctype":"Purchase Invoice","source_parent_name":doc.name,"source_parent_row":original.source_row,"reverses_event_key":original.event_key,"original_event_key":original.event_key,"commitment_effect":"Decrease Open Commitment","matching_status":"Fully Matched" if abs(need-take)<=EPSILON else "Partially Matched","matching_key":key,"gl_entry":gl.name,"remarks":"Eligible GL consumed exactly once"})
                from qorg.qorg.finance_period_control.cross_period import stamp_actual_event
                stamp_actual_event(ev,doc.company,gl.posting_date,original.project);available[gl.name]-=take;need-=take
            original.matching_status="Fully Matched" if need<=EPSILON else "Partially Matched" if need<flt(original.base_amount) else "Pending GL"
        ledger.save(ignore_permissions=True)
    return {"invoice":doc.name,"unmatched_gl":{k:v for k,v in available.items() if v>EPSILON}}
def reconcile_on_update_after_submit(doc,method=None):
    if doc.docstatus==1:return reconcile(doc,method)
