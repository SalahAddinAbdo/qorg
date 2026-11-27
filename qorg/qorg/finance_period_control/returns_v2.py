import frappe
from frappe.utils import flt
from qorg.qorg.finance_period_control.source_reconciliation import EPSILON,row_amount_snapshot,row_budget_line
from qorg.qorg.finance_period_control.returns_amendments import _adjustment,_reverse_capacity

def _ledgers_for_original(doctype,name,row_name=None):
    filters={"entries.reference_doctype":doctype,"entries.reference_name":name}
    if row_name:filters["entries.source_row"]=row_name
    return frappe.get_all("Commitment Ledger",filters=filters,pluck="name",distinct=True)
def invoice_return(doc,method=None):
    original_name=doc.get("return_against")
    if not original_name:frappe.throw("Purchase return/credit note requires Return Against")
    for row in doc.items:
        original_row=row.get("purchase_invoice_item") or row.get("pi_detail");remaining=row_amount_snapshot(doc,row)["base_amount"]
        ledgers=_ledgers_for_original("Purchase Invoice",original_name,original_row)
        if not ledgers:frappe.throw(f"No reversible invoice commitment found for return row {row.idx}")
        for name in ledgers:
            ledger=frappe.get_doc("Commitment Ledger",name)
            candidates=[e for e in ledger.entries if e.reference_doctype=="Purchase Invoice" and e.reference_name==original_name and e.stage=="Invoiced" and e.direction=="Increase" and (not original_row or e.source_row==original_row)]
            for original in candidates:
                take=min(remaining,_reverse_capacity(ledger,original))
                if take>EPSILON:_adjustment(ledger,doc,row,original,take,"Credit Note","Invoice return reverses original commitment");remaining-=take
                if remaining<=EPSILON:break
            ledger.save(ignore_permissions=True)
            if remaining<=EPSILON:break
        if remaining>EPSILON:frappe.throw(f"Return exceeds reversible amount for row {row.idx}")
    return True

def close_purchase_order(doc,method=None):
    if (doc.get("status") or "").lower() not in ("closed","stopped"):return
    for row in doc.items:
        for name in _ledgers_for_original("Purchase Order",doc.name,row.name):
            ledger=frappe.get_doc("Commitment Ledger",name)
            for original in [e for e in ledger.entries if e.reference_doctype=="Purchase Order" and e.reference_name==doc.name and e.source_row==row.name and e.stage=="Ordered" and e.direction=="Increase"]:
                remaining=_reverse_capacity(ledger,original)
                if remaining>EPSILON:_adjustment(ledger,doc,row,original,remaining,"Closure Release","PO closed/stopped; unused commitment released")
            ledger.save(ignore_permissions=True)
