import frappe
from frappe.utils import flt, getdate, today

STAGE_FIELDS={"Requested":"requested","Reserved":"reserved","Ordered":"ordered","Contracted":"contracted","Accepted":"accepted","Invoiced":"invoiced","Paid":"paid"}
TERMINAL_STAGES={"Released","Cancelled"}

def make_event_key(reference_doctype,reference_name,stage,direction="Increase",source_row=None):
    parts=[reference_doctype or "",reference_name or "",source_row or "",stage or "",direction or ""]
    return "|".join(str(x).strip() for x in parts)

def validate_lifecycle(doc):
    totals={v:0.0 for v in STAGE_FIELDS.values()};seen=set();last_date=None
    for row in doc.get("entries") or []:
        if flt(row.amount)<=0: frappe.throw("Commitment Entry amount must be greater than zero")
        key=row.event_key or make_event_key(row.reference_doctype,row.reference_name,row.stage,row.direction,row.source_row)
        row.event_key=key
        if key in seen: frappe.throw(f"Duplicate commitment lifecycle event: {key}")
        seen.add(key)
        if row.direction=="Decrease" and not row.reverses_event_key: frappe.throw("Decrease events must identify Reverses Event Key")
        if row.reverses_event_key and row.reverses_event_key not in seen:
            # Existing earlier database events are allowed; unresolved references are not.
            exists=doc.name and frappe.db.exists("Commitment Entry",{"parent":doc.name,"event_key":row.reverses_event_key})
            if not exists: frappe.throw(f"Reversed lifecycle event was not found: {row.reverses_event_key}")
        field=STAGE_FIELDS.get(row.stage)
        if field: totals[field]+=flt(row.amount)*(1 if row.direction=="Increase" else -1)
        last_date=max(filter(None,[last_date,getdate(row.posting_date)])) if last_date else getdate(row.posting_date)
    for field,value in totals.items():
        if value < -0.000001: frappe.throw(f"Commitment stage cannot have a negative balance: {field}")
        doc.set(field,value)
    from qorg.qorg.finance_period_control.source_reconciliation import rebuild_open_commitment
    releases=sum(flt(r.base_amount or r.amount)*(1 if r.direction=="Increase" else -1) for r in (doc.get("entries") or []) if r.stage=="Released")
    doc.open_commitment=max(rebuild_open_commitment(doc)-max(releases,0),0)
    doc.last_lifecycle_date=last_date
    last=(doc.get("entries") or [])[-1] if doc.get("entries") else None
    if last:
        doc.last_reference_doctype=last.reference_doctype;doc.last_reference_name=last.reference_name
    if doc.docstatus==2 or (last and last.stage=="Cancelled"): doc.lifecycle_status="Cancelled"
    elif doc.open_commitment>0: doc.lifecycle_status="Active"
    elif doc.get("entries") and releases>0: doc.lifecycle_status="Fully Released"
    elif doc.get("entries"): doc.lifecycle_status="Closed"
    else: doc.lifecycle_status="Draft"

def append_event(doc,stage,reference_doctype,reference_name,amount,direction="Increase",posting_date=None,remarks=None,source_row=None,reverses_event_key=None,source_modified=None):
    if stage not in set(STAGE_FIELDS)|TERMINAL_STAGES|{"Planned","Received"}: frappe.throw("Unsupported commitment stage")
    key=make_event_key(reference_doctype,reference_name,stage,direction,source_row)
    existing=[r for r in (doc.get("entries") or []) if r.event_key==key]
    if existing: return existing[0]
    row=doc.append("entries",{"stage":stage,"posting_date":posting_date or today(),"reference_doctype":reference_doctype,"reference_name":reference_name,"amount":amount,"direction":direction,"remarks":remarks,"event_key":key,"source_row":source_row,"reverses_event_key":reverses_event_key,"source_modified":source_modified})
    validate_lifecycle(doc);return row

@frappe.whitelist()
def release_commitment(ledger,amount,reference_doctype,reference_name,posting_date=None,remarks=None,reverses_event_key=None):
    doc=frappe.get_doc("Commitment Ledger",ledger);doc.check_permission("write")
    if flt(amount)>flt(doc.open_commitment): frappe.throw("Release amount exceeds the open commitment")
    append_event(doc,"Released",reference_doctype,reference_name,amount,"Increase",posting_date,remarks,reverses_event_key=reverses_event_key)
    doc.save();return {"ledger":doc.name,"open_commitment":doc.open_commitment,"status":doc.lifecycle_status}
