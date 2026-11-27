import frappe
from frappe.utils import flt
from qorg.qorg.finance_period_control.source_reconciliation import EPSILON

def _invoice_row_weights(invoice):
    rows=[r for r in invoice.items if (r.get("budget_line") or r.get("custom_budget_line"))]
    total=sum(abs(flt(r.get("base_net_amount") or r.get("base_amount"))) for r in rows)
    return rows,total

def payment_submit(doc,method=None):
    # Information only, allocated once across invoice rows by base net value.
    for ref in doc.references:
        if ref.reference_doctype!="Purchase Invoice" or flt(ref.allocated_amount)<=EPSILON:continue
        inv=frappe.get_doc("Purchase Invoice",ref.reference_name);rows,total=_invoice_row_weights(inv)
        remaining=flt(ref.allocated_amount)
        for idx,row in enumerate(rows):
            amount=remaining if idx==len(rows)-1 else flt(ref.allocated_amount)*(abs(flt(row.get("base_net_amount") or row.get("base_amount")))/total if total else 1/len(rows));remaining-=amount
            ledger_names=frappe.get_all("Commitment Ledger",filters={"entries.reference_doctype":"Purchase Invoice","entries.reference_name":inv.name,"entries.source_row":row.name},pluck="name",distinct=True)
            for name in ledger_names:
                ledger=frappe.get_doc("Commitment Ledger",name);key=f"PAYINFO|{doc.name}|{ref.name}|{row.name}|{ledger.name}"
                if any(e.event_key==key for e in ledger.entries):continue
                original=next((e for e in ledger.entries if e.reference_doctype=="Purchase Invoice" and e.reference_name==inv.name and e.source_row==row.name and e.stage=="Invoiced" and e.direction=="Increase"),None)
                if not original:continue
                ledger.append("entries",{"stage":"Paid","posting_date":doc.posting_date,"reference_doctype":"Payment Entry","reference_name":doc.name,"source_row":ref.name,"event_key":key,"amount":amount,"base_amount":amount,"company_currency":original.company_currency,"direction":"Increase","budget_line":original.budget_line,"project":original.project,"funding_agreement":original.funding_agreement,"donor":original.donor,"cost_distribution_row":original.cost_distribution_row,"source_parent_doctype":"Purchase Invoice Item","source_parent_name":inv.name,"source_parent_row":row.name,"commitment_effect":"Information Only","matching_status":"Not Applicable","remarks":"Payment allocated to invoice row; no budget effect"});ledger.save(ignore_permissions=True)

def _copy_reversal(original,doc,key,direction):
    fields=("stage","amount","base_amount","company_currency","transaction_currency","transaction_amount","conversion_rate","net_base_amount","tax_base_amount","charge_base_amount","discount_base_amount","amount_policy","budget_line","project","funding_agreement","donor","cost_distribution_row","cost_distribution_ledger","allocation_percentage","distribution_snapshot","commitment_period","actual_period","origin_period","control_policy","source_parent_doctype","source_parent_name","source_parent_row")
    data={f:original.get(f) for f in fields};data.update({"posting_date":doc.get("posting_date") or frappe.utils.today(),"reference_doctype":doc.doctype,"reference_name":doc.name,"source_row":original.source_row,"event_key":key,"direction":direction,"reverses_event_key":original.event_key,"original_event_key":original.event_key,"adjustment_type":"Cancellation","adjustment_period":None,"commitment_effect":"Decrease Open Commitment" if direction=="Decrease" and original.stage in ("Requested","Reserved","Ordered","Contracted","Invoiced") else "Increase Open Commitment" if direction=="Increase" and original.stage in ("Requested","Reserved","Ordered","Contracted","Invoiced") else "Information Only","remarks":"Exact automatic cancellation reversal"});return data

def cancel_source(doc,method=None):
    for name in frappe.get_all("Commitment Ledger",filters={"entries.reference_doctype":doc.doctype,"entries.reference_name":doc.name},pluck="name",distinct=True):
        ledger=frappe.get_doc("Commitment Ledger",name)
        originals=[e for e in list(ledger.entries) if e.reference_doctype==doc.doctype and e.reference_name==doc.name and e.adjustment_type!="Cancellation"]
        for original in originals:
            key=f"CANCEL|{doc.doctype}|{doc.name}|{original.event_key}"
            if any(e.event_key==key for e in ledger.entries):continue
            ledger.append("entries",_copy_reversal(original,doc,key,"Decrease" if original.direction=="Increase" else "Increase"))
        ledger.save(ignore_permissions=True)
