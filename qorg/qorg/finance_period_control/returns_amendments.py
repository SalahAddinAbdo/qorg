import frappe
from frappe.utils import flt
from qorg.qorg.finance_period_control.source_reconciliation import EPSILON, COMMITMENT_STAGES, _ledger, _process_for_po, row_budget_line, row_amount_snapshot, event_key
from qorg.qorg.finance_period_control.service import resolve_budget_period, get_control_policy


def _period(company,date,project=None):
    if get_control_policy(company,project)=="Disabled":return None
    try:return resolve_budget_period(company,date,project,require_open=False)[0].name
    except Exception:return None

def _reverse_capacity(ledger,event):
    reversed_amount=sum(flt(x.base_amount or x.amount) for x in ledger.entries if x.reverses_event_key==event.event_key)
    return max(flt(event.base_amount or event.amount)-reversed_amount,0)

def _adjustment(ledger,source_doc,row,original,amount,kind,remarks):
    amount=min(abs(flt(amount)),_reverse_capacity(ledger,original))
    if amount<=EPSILON:return None
    key=f"ADJUST|{kind}|{source_doc.doctype}|{source_doc.name}|{row.name}|{original.event_key}|{amount:.6f}"
    if any(x.event_key==key for x in ledger.entries):return None
    direction="Decrease" if original.direction=="Increase" else "Increase"
    period=_period(source_doc.company,source_doc.get("posting_date") or frappe.utils.today(),row.get("project") or source_doc.get("project"))
    return ledger.append("entries",{"stage":original.stage,"posting_date":source_doc.get("posting_date") or frappe.utils.today(),"reference_doctype":source_doc.doctype,"reference_name":source_doc.name,"source_row":row.name,"event_key":key,"amount":amount,"base_amount":amount,"company_currency":original.company_currency,"transaction_currency":source_doc.get("currency"),"transaction_amount":abs(flt(row.get("net_amount") or row.get("amount"))),"conversion_rate":flt(source_doc.get("conversion_rate") or 1),"direction":direction,"budget_line":original.budget_line,"project":original.project,"source_parent_doctype":original.reference_doctype,"source_parent_name":original.reference_name,"source_parent_row":original.source_row,"reverses_event_key":original.event_key,"original_event_key":original.event_key,"commitment_effect":"Decrease Open Commitment" if original.stage in COMMITMENT_STAGES and direction=="Decrease" else "Increase Open Commitment" if original.stage in COMMITMENT_STAGES else "Information Only","adjustment_type":kind,"return_against":source_doc.get("return_against"),"amended_from":source_doc.get("amended_from"),"source_version":source_doc.get("amendment_date") and 1 or 0,"remaining_reversible_amount":max(_reverse_capacity(ledger,original)-amount,0),"adjustment_period":period,"commitment_period":original.commitment_period,"actual_period":period if original.reference_doctype=="GL Entry" else None,"origin_period":original.origin_period or original.commitment_period,"remarks":remarks})

def purchase_invoice_return_submit(doc,method=None):
    if not doc.get("is_return"):return False
    original_name=doc.get("return_against")
    if not original_name:frappe.throw("Purchase return/credit note requires Return Against")
    for row in doc.items:
        bl=row_budget_line(row);po=row.get("purchase_order");process=_process_for_po(po)
        if not(bl and process):continue
        ledger=_ledger(process,doc.company,row.get("project") or doc.get("project"),doc.currency,bl)
        original_row=row.get("purchase_invoice_item") or row.get("pi_detail")
        candidates=[x for x in ledger.entries if x.reference_doctype=="Purchase Invoice" and x.reference_name==original_name and x.stage=="Invoiced" and x.direction=="Increase" and (not original_row or x.source_row==original_row)]
        remaining=row_amount_snapshot(doc,row)["base_amount"]
        for original in candidates:
            used=min(remaining,_reverse_capacity(ledger,original));_adjustment(ledger,doc,row,original,used,"Credit Note","Purchase Invoice return reverses original invoiced commitment");remaining-=used
            if remaining<=EPSILON:break
        if remaining>EPSILON:frappe.throw(f"Return amount exceeds reversible invoiced amount for row {row.idx}")
        ledger.save(ignore_permissions=True)
    return True

def purchase_receipt_return_submit(doc,method=None):
    if not doc.get("is_return"):return False
    original_name=doc.get("return_against")
    for row in doc.items:
        bl=row_budget_line(row);process=_process_for_po(row.get("purchase_order"))
        if not(bl and process):continue
        ledger=_ledger(process,doc.company,row.get("project") or doc.get("project"),doc.currency,bl)
        original_row=row.get("purchase_receipt_item") or row.get("pr_detail")
        candidates=[x for x in ledger.entries if x.reference_doctype=="Purchase Receipt" and x.reference_name==original_name and x.stage=="Received" and x.direction=="Increase" and (not original_row or x.source_row==original_row)]
        remaining=row_amount_snapshot(doc,row)["base_amount"]
        for original in candidates:
            used=min(remaining,_reverse_capacity(ledger,original));_adjustment(ledger,doc,row,original,used,"Purchase Return","Purchase Receipt return reverses receipt information");remaining-=used
            if remaining<=EPSILON:break
        if remaining>EPSILON:frappe.throw(f"Return quantity/value exceeds reversible receipt for row {row.idx}")
        ledger.save(ignore_permissions=True)
    return True

def amendment_submit(doc,normal_handler):
    if not doc.get("amended_from"):return normal_handler(doc,None)
    # The cancelled predecessor is reversed by its on_cancel hook. The amended document
    # receives fresh row-level events carrying its lineage, never mutating history.
    result=normal_handler(doc,None)
    for ledger_name in frappe.get_all("Commitment Ledger",filters={"entries.reference_doctype":doc.doctype,"entries.reference_name":doc.name},pluck="name",distinct=True):
        ledger=frappe.get_doc("Commitment Ledger",ledger_name)
        for e in ledger.entries:
            if e.reference_doctype==doc.doctype and e.reference_name==doc.name and e.adjustment_type in (None,"","Original"):
                e.adjustment_type="Amendment";e.amended_from=doc.amended_from;e.source_version=1
        ledger.save(ignore_permissions=True)
    return result

def purchase_order_close_or_stop(doc,method=None):
    status=(doc.get("status") or "").lower()
    if status not in ("closed","stopped"):return
    for row in doc.items:
        bl=row_budget_line(row);process=_process_for_po(doc.name)
        if not(bl and process):continue
        ledger=_ledger(process,doc.company,row.get("project") or doc.get("project"),doc.currency,bl)
        originals=[x for x in ledger.entries if x.reference_doctype=="Purchase Order" and x.reference_name==doc.name and x.source_row==row.name and x.stage=="Ordered" and x.direction=="Increase"]
        for original in originals:
            remaining=_reverse_capacity(ledger,original)
            if remaining>EPSILON:_adjustment(ledger,doc,row,original,remaining,"Closure Release",f"Purchase Order {status} releases unused row commitment")
        ledger.save(ignore_permissions=True)

def purchase_order_reopen(doc,method=None):
    status=(doc.get("status") or "").lower()
    if status in ("closed","stopped"):return
    # Reopening reverses prior closure releases only; normal Ordered events stay immutable.
    for ledger_name in frappe.get_all("Commitment Ledger",filters={"entries.reference_doctype":"Purchase Order","entries.reference_name":doc.name},pluck="name",distinct=True):
        ledger=frappe.get_doc("Commitment Ledger",ledger_name)
        releases=[x for x in ledger.entries if x.reference_doctype=="Purchase Order" and x.reference_name==doc.name and x.adjustment_type=="Closure Release"]
        for release in releases:
            if any(x.reverses_event_key==release.event_key for x in ledger.entries):continue
            row=next((r for r in doc.items if r.name==release.source_row),None)
            if row:_adjustment(ledger,doc,row,release,flt(release.base_amount),"Amendment","Purchase Order reopened; closure release reversed")
        ledger.save(ignore_permissions=True)
