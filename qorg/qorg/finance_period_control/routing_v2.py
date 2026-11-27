"""Row-level routing for linked, direct, and distributed procurement rows."""
import frappe
from qorg.qorg.finance_period_control import source_reconciliation as sr
from qorg.qorg.finance_period_control.distribution_bridge import append_distributed, _rows
from qorg.qorg.finance_period_control.returns_amendments import amendment_submit, purchase_invoice_return_submit, purchase_receipt_return_submit


def _po_linked(row): return bool(row.get("material_request") or row.get("material_request_item"))
def _pi_linked(row): return bool(row.get("purchase_order") or row.get("po_detail"))
def _require_direct(doc, rows):
    if not rows:return
    if not doc.get("qorg_direct_procurement"):frappe.throw("Unlinked rows require Direct Procurement: "+", ".join(str(r.idx) for r in rows))
    if not doc.get("qorg_direct_procurement_reason") or not doc.get("qorg_direct_approval_reference"):frappe.throw("Direct Procurement Reason and Approval Reference are required")
    missing=[str(r.idx) for r in rows if not sr.row_budget_line(r) or not (r.get("project") or doc.get("project"))]
    if missing:frappe.throw("Budget Line and Project are required for direct rows: "+", ".join(missing))

def validate(doc,method=None):
    if doc.get("is_return"):return
    direct=[r for r in doc.items if not (_po_linked(r) if doc.doctype=="Purchase Order" else _pi_linked(r))]
    _require_direct(doc,direct)

def material_request_submit(doc,method=None):
    if doc.material_request_type!="Purchase":return
    process=doc.get("custom_procurement_process") or sr._process_for_mr(doc.name)
    if not process:return
    for row in doc.items:
        if _rows(doc,row.name):append_distributed("Requested",doc,row,"Increase","Increase Open Commitment","Distributed Material Request submitted")
        else:
            bl=sr.row_budget_line(row)
            if not bl:continue
            ledger=sr._ledger(process,doc.company,row.get("project") or doc.get("project"),doc.get("currency") or frappe.get_cached_value("Company",doc.company,"default_currency"),bl,doc.name)
            snap=sr.row_amount_snapshot(doc,row);sr._append(ledger,"Requested",doc,row,snap["base_amount"],"Increase","Increase Open Commitment",remarks="Material Request row submitted",snapshot=snap);ledger.save(ignore_permissions=True)

def _release_upstream(source_doctype,source_row,stage,doc,row,amount):
    if not source_row:return
    names=frappe.get_all("Commitment Ledger",filters={"entries.reference_doctype":source_doctype,"entries.source_row":source_row,"entries.stage":stage,"entries.direction":"Increase"},pluck="name",distinct=True)
    remaining=amount
    for name in names:
        ledger=frappe.get_doc("Commitment Ledger",name)
        originals=[e for e in ledger.entries if e.reference_doctype==source_doctype and e.source_row==source_row and e.stage==stage and e.direction=="Increase"]
        for original in originals:
            reversed_amount=sum(frappe.utils.flt(x.base_amount or x.amount) for x in ledger.entries if x.reverses_event_key==original.event_key)
            available=max(frappe.utils.flt(original.base_amount or original.amount)-reversed_amount,0)
            take=min(available,remaining)
            if take>sr.EPSILON:
                proxy=frappe._dict(row.as_dict());proxy.budget_line=original.budget_line;proxy.project=original.project
                event=sr._append(ledger,stage,doc,proxy,take,"Decrease","Decrease Open Commitment",source_doctype,source_row,f"Converted by {doc.doctype} {doc.name}")
                if event:event.reverses_event_key=original.event_key;event.original_event_key=original.event_key
                remaining-=take
            if remaining<=sr.EPSILON:break
        ledger.save(ignore_permissions=True)
        if remaining<=sr.EPSILON:break
    if remaining>sr.EPSILON:frappe.throw(f"Upstream {stage} balance is insufficient for source row {source_row}")

def purchase_order_submit(doc,method=None):
    linked=[r for r in doc.items if _po_linked(r)];direct=[r for r in doc.items if not _po_linked(r)];_require_direct(doc,direct)
    for row in linked+direct:
        snap=sr.row_amount_snapshot(doc,row)
        if _rows(doc,row.name) or row in direct:append_distributed("Ordered",doc,row,"Increase","Increase Open Commitment","Direct/distributed Purchase Order submitted", "Material Request Item" if row.get("material_request_item") else None,row.get("material_request_item"))
        else:
            process=sr._process_for_mr(row.get("material_request"));bl=sr.row_budget_line(row)
            if not(process and bl):frappe.throw(f"Procurement Process and Budget Line are required for linked PO row {row.idx}")
            ledger=sr._ledger(process,doc.company,row.get("project") or doc.get("project"),doc.currency,bl,row.get("material_request"));sr._append(ledger,"Ordered",doc,row,snap["base_amount"],"Increase","Increase Open Commitment","Material Request Item",row.get("material_request_item"),"Purchase Order row submitted",snap);ledger.save(ignore_permissions=True)
        if row.get("material_request_item"):_release_upstream("Material Request",row.material_request_item,"Requested",doc,row,snap["base_amount"])

def purchase_invoice_submit(doc,method=None):
    from qorg.qorg.finance_period_control.gl_matching_v2 import reconcile
    if doc.get("is_return"):
        from qorg.qorg.finance_period_control.returns_v2 import invoice_return
        invoice_return(doc,method)
        return reconcile(doc)
    linked=[r for r in doc.items if _pi_linked(r)];direct=[r for r in doc.items if not _pi_linked(r)];_require_direct(doc,direct)
    for row in linked+direct:
        snap=sr.row_amount_snapshot(doc,row)
        if _rows(doc,row.name) or row in direct:append_distributed("Invoiced",doc,row,"Increase","Increase Open Commitment","Direct/distributed invoice pending GL","Purchase Order Item" if row.get("po_detail") else None,row.get("po_detail"))
        else:
            process=sr._process_for_po(row.get("purchase_order"));bl=sr.row_budget_line(row)
            if not(process and bl):frappe.throw(f"Procurement Process and Budget Line are required for linked PI row {row.idx}")
            ledger=sr._ledger(process,doc.company,row.get("project") or doc.get("project"),doc.currency,bl);sr._append(ledger,"Invoiced",doc,row,snap["base_amount"],"Increase","Increase Open Commitment","Purchase Order Item",row.get("po_detail"),"Invoice pending GL",snap);ledger.save(ignore_permissions=True)
        if row.get("po_detail"):_release_upstream("Purchase Order",row.po_detail,"Ordered",doc,row,snap["base_amount"])
    return reconcile(doc)

def purchase_receipt_submit(doc,method=None):
    if doc.get("is_return"):return purchase_receipt_return_submit(doc,method)
    for row in doc.items:
        if _rows(doc,row.name):append_distributed("Received",doc,row,"Increase","Information Only","Distributed receipt information","Purchase Order Item",row.get("purchase_order_item"))
        else:sr.purchase_receipt_submit(frappe._dict(doc.as_dict()|{"items":[row]}))
