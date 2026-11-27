import frappe
from frappe.utils import flt, getdate

COMMITMENT_STAGES={"Requested","Reserved","Ordered","Contracted","Invoiced"}
INFO_STAGES={"Received","Accepted","Paid"}
EPSILON=0.005

def row_amount_snapshot(doc,row):
    from qorg.qorg.finance_period_control.amount_policy import calculate_row_amount
    return calculate_row_amount(doc,row,row_budget_line(row))

def row_base_amount(row,doc=None):
    if doc:return row_amount_snapshot(doc,row)["base_amount"]
    return abs(flt(row.get("base_net_amount") or row.get("base_amount") or row.get("base_rate"))*flt(row.get("qty") or 1)) if not row.get("base_net_amount") else abs(flt(row.base_net_amount))

def row_budget_line(row):
    return row.get("budget_line") or row.get("custom_budget_line")

def event_key(doctype,name,row_name,stage,direction): return "|".join((doctype,name,row_name or "",stage,direction))

def _process_for_mr(mr): return mr and frappe.db.get_value("Procurement Process",{"material_request":mr},"name")
def _process_for_po(po):
    if not po:return None
    process=frappe.db.get_value("Award Decision",{"purchase_order":po,"docstatus":1},"procurement_process")
    if process:return process
    mr=frappe.db.get_value("Purchase Order Item",{"parent":po,"parenttype":"Purchase Order","material_request":["is","set"]},"material_request")
    return _process_for_mr(mr)

def _ledger(process,company,project,currency,budget_line,material_request=None):
    key={"procurement_process":process,"budget_line":budget_line} if process and budget_line else {"procurement_process":process}
    name=process and frappe.db.get_value("Commitment Ledger",key,"name")
    doc=frappe.get_doc("Commitment Ledger",name) if name else frappe.new_doc("Commitment Ledger")
    if doc.is_new():doc.update({"company":company,"project":project,"currency":currency,"procurement_process":process,"material_request":material_request,"budget_line":budget_line})
    return doc

def _existing(doc,key):return next((r for r in doc.get("entries") or [] if r.event_key==key),None)
def _append(doc,stage,source_doc,row,amount,direction,effect,upstream_doctype=None,upstream_row=None,remarks=None,snapshot=None):
    if amount<=EPSILON:return None
    snapshot=snapshot or {}
    key=event_key(source_doc.doctype,source_doc.name,row.name,stage,direction)
    if _existing(doc,key):return None
    event=doc.append("entries",{"stage":stage,"posting_date":source_doc.get("posting_date") or source_doc.get("transaction_date") or source_doc.get("schedule_date") or frappe.utils.today(),"reference_doctype":source_doc.doctype,"reference_name":source_doc.name,"source_row":row.name,"event_key":key,"amount":amount,"base_amount":amount,"company_currency":snapshot.get("company_currency") or frappe.get_cached_value("Company",source_doc.company,"default_currency"),"transaction_currency":snapshot.get("transaction_currency"),"transaction_amount":snapshot.get("transaction_amount"),"conversion_rate":snapshot.get("conversion_rate") or 1,"net_base_amount":snapshot.get("net_base_amount"),"tax_base_amount":snapshot.get("tax_base_amount"),"charge_base_amount":snapshot.get("charge_base_amount"),"discount_base_amount":snapshot.get("discount_base_amount"),"amount_policy":snapshot.get("amount_policy"),"direction":direction,"budget_line":row_budget_line(row),"project":row.get("project") or source_doc.get("project"),"source_parent_doctype":upstream_doctype,"source_parent_name":row.get("purchase_order") or row.get("material_request") or source_doc.get("return_against") or source_doc.get("amended_from"),"source_parent_row":upstream_row,"commitment_effect":effect,"matching_status":"Pending GL" if stage=="Invoiced" and direction=="Increase" else "Not Applicable","remarks":remarks})
    from qorg.qorg.finance_period_control.cross_period import stamp_commitment_event
    return stamp_commitment_event(event,source_doc,row.get("project") or source_doc.get("project"))

def _remaining_for_row(ledger,stage,source_row):
    inc=sum(flt(r.base_amount or r.amount) for r in ledger.entries if r.stage==stage and r.source_row==source_row and r.direction=="Increase")
    dec=sum(flt(r.base_amount or r.amount) for r in ledger.entries if r.stage==stage and r.source_parent_row==source_row and r.direction=="Decrease")
    return max(inc-dec,0)

def material_request_submit(doc,method=None):
    if doc.material_request_type!="Purchase":return
    process=doc.get("custom_procurement_process") or _process_for_mr(doc.name)
    if not process:return
    for row in doc.items:
        bl=row_budget_line(row)
        if not bl:continue
        ledger=_ledger(process,doc.company,row.get("project") or doc.get("project"),doc.get("currency") or frappe.get_cached_value("Company",doc.company,"default_currency"),bl,doc.name)
        _append(ledger,"Requested",doc,row,row_base_amount(row,doc),"Increase","Increase Open Commitment",remarks="Material Request row submitted",snapshot=row_amount_snapshot(doc,row))
        ledger.save(ignore_permissions=True)

def purchase_order_submit(doc,method=None):
    grouped={}
    for row in doc.items:
        bl=row_budget_line(row);process=_process_for_mr(row.get("material_request"))
        if not (bl and process):continue
        ledger=grouped.setdefault((process,bl),_ledger(process,doc.company,row.get("project") or doc.get("project"),doc.currency,bl,row.get("material_request")))
        snapshot=row_amount_snapshot(doc,row);amount=snapshot["base_amount"]
        _append(ledger,"Ordered",doc,row,amount,"Increase","Increase Open Commitment",upstream_doctype="Material Request Item",upstream_row=row.get("material_request_item"),remarks="Purchase Order row submitted",snapshot=snapshot)
        if row.get("material_request_item"):
            release=min(amount,_remaining_for_row(ledger,"Requested",row.material_request_item))
            _append(ledger,"Requested",doc,row,release,"Decrease","Decrease Open Commitment",upstream_doctype="Material Request Item",upstream_row=row.material_request_item,remarks="Requested amount converted to Purchase Order")
    for ledger in grouped.values():ledger.save(ignore_permissions=True)

def purchase_receipt_submit(doc,method=None):
    for row in doc.items:
        process=_process_for_po(row.get("purchase_order"));bl=row_budget_line(row)
        if not(process and bl):continue
        ledger=_ledger(process,doc.company,row.get("project") or doc.get("project"),doc.currency,bl)
        _append(ledger,"Received",doc,row,row_base_amount(row,doc),"Increase","Information Only",upstream_doctype="Purchase Order Item",upstream_row=row.get("purchase_order_item"),remarks="Receipt does not consume budget unless recognized by eligible GL Entry",snapshot=row_amount_snapshot(doc,row))
        ledger.save(ignore_permissions=True)

def purchase_invoice_submit(doc,method=None):
    grouped={}
    for row in doc.items:
        process=_process_for_po(row.get("purchase_order"));bl=row_budget_line(row)
        if not(process and bl):continue
        ledger=grouped.setdefault((process,bl),_ledger(process,doc.company,row.get("project") or doc.get("project"),doc.currency,bl))
        snapshot=row_amount_snapshot(doc,row);amount=snapshot["base_amount"]
        _append(ledger,"Invoiced",doc,row,amount,"Increase","Increase Open Commitment",upstream_doctype="Purchase Order Item",upstream_row=row.get("po_detail"),remarks="Invoice commitment pending eligible GL match",snapshot=snapshot)
        if row.get("po_detail"):
            release=min(amount,_remaining_for_row(ledger,"Ordered",row.po_detail))
            _append(ledger,"Ordered",doc,row,release,"Decrease","Decrease Open Commitment",upstream_doctype="Purchase Order Item",upstream_row=row.po_detail,remarks="Ordered amount realized by Purchase Invoice")
    for ledger in grouped.values():ledger.save(ignore_permissions=True)

def payment_submit(doc,method=None):
    # Payment is settlement of payable, never new budget consumption.
    for ref in doc.references:
        if ref.reference_doctype!="Purchase Invoice":continue
        inv=frappe.get_doc("Purchase Invoice",ref.reference_name)
        for row in inv.items:
            process=_process_for_po(row.get("purchase_order"));bl=row_budget_line(row)
            if not(process and bl):continue
            ledger=_ledger(process,doc.company,row.get("project") or inv.get("project"),doc.paid_from_account_currency or frappe.get_cached_value("Company",doc.company,"default_currency"),bl)
            proxy=frappe._dict(name=f"{ref.name}-{row.name}",get=lambda key,default=None:{"project":row.get("project")}.get(key,default))
            _append(ledger,"Paid",doc,proxy,flt(ref.allocated_amount),"Increase","Information Only",upstream_doctype="Purchase Invoice Item",upstream_row=row.name,remarks="Payment information only; no budget effect")
            ledger.save(ignore_permissions=True)

def cancel_source(doc,method=None):
    for name in frappe.get_all("Commitment Ledger",filters={"entries.reference_doctype":doc.doctype,"entries.reference_name":doc.name},pluck="name",distinct=True):
        ledger=frappe.get_doc("Commitment Ledger",name)
        originals=[r for r in ledger.entries if r.reference_doctype==doc.doctype and r.reference_name==doc.name and not str(r.event_key or '').endswith('|Cancellation')]
        for r in originals:
            key=f"{r.event_key}|Cancellation"
            if _existing(ledger,key):continue
            ledger.append("entries",{"stage":r.stage,"posting_date":frappe.utils.today(),"reference_doctype":doc.doctype,"reference_name":doc.name,"source_row":r.source_row,"event_key":key,"amount":r.amount,"base_amount":r.base_amount,"company_currency":r.company_currency,"direction":"Decrease" if r.direction=="Increase" else "Increase","budget_line":r.budget_line,"project":r.project,"source_parent_doctype":r.source_parent_doctype,"source_parent_row":r.source_parent_row,"reverses_event_key":r.event_key,"commitment_effect":"Decrease Open Commitment" if r.direction=="Increase" and r.stage in COMMITMENT_STAGES else "Increase Open Commitment" if r.direction=="Decrease" and r.stage in COMMITMENT_STAGES else "Information Only","remarks":"Automatic exact reversal on cancellation"})
        ledger.save(ignore_permissions=True)

def rebuild_open_commitment(doc):
    balances={s:0.0 for s in COMMITMENT_STAGES}
    for r in doc.get("entries") or []:
        if r.stage not in COMMITMENT_STAGES:continue
        balances[r.stage]+=flt(r.base_amount or r.amount)*(1 if r.direction=="Increase" else -1)
    for stage,value in balances.items():
        if value < -EPSILON:frappe.throw(f"Negative open commitment at stage {stage}")
    return sum(max(v,0) for v in balances.values())
