import json
import frappe
from frappe.utils import flt
from qorg.qorg.finance_period_control.source_reconciliation import _ledger,_append,row_amount_snapshot,row_budget_line,EPSILON

TABLE_FIELD="custom_cost_distributions"

def _rows(doc,source_row):
    if not doc.meta.has_field(TABLE_FIELD):return []
    return [r for r in (doc.get(TABLE_FIELD) or []) if r.source_row==source_row]

def split_snapshot(doc,row):
    source=row_amount_snapshot(doc,row);dist=_rows(doc,row.name)
    if not dist:return [{"target":None,"snapshot":source}]
    total=sum(flt(x.allocated_amount) for x in dist)
    if abs(total-source["base_amount"])>0.01:frappe.throw(f"Cost distribution for source row {row.idx} must equal eligible base amount {source['base_amount']}; found {total}")
    result=[];remaining={k:flt(source.get(k)) for k in ("base_amount","net_base_amount","tax_base_amount","charge_base_amount","discount_base_amount")}
    for idx,target in enumerate(dist):
        ratio=flt(target.allocated_amount)/total if total else 0;snap=dict(source)
        for key in remaining:
            value=remaining[key] if idx==len(dist)-1 else flt(source.get(key))*ratio;snap[key]=value;remaining[key]-=value
        snap["transaction_amount"]=flt(source.get("transaction_amount"))*ratio
        result.append({"target":target,"snapshot":snap})
    return result

def _target_value(target,name,fallback=None):return target.get(name) if target and target.get(name) not in (None,"") else fallback

def validate_distribution(doc,method=None):
    if not doc.meta.has_field(TABLE_FIELD) or not doc.get(TABLE_FIELD):return
    source_names={r.name for r in doc.items};grouped={}
    for target in doc.get(TABLE_FIELD):
        if target.source_row not in source_names:frappe.throw(f"Unknown source row in cost distribution: {target.source_row}")
        grouped.setdefault(target.source_row,[]).append(target)
        if not target.project or not target.budget_line:frappe.throw("Every distributed target requires Project and Budget Line")
        if target.funding_agreement:
            agreement=frappe.get_doc("Funding Agreement",target.funding_agreement)
            if agreement.project and agreement.project!=target.project:frappe.throw("Funding Agreement Project does not match distributed Project")
            if target.donor and agreement.donor and target.donor!=agreement.donor:frappe.throw("Distributed Donor does not match Funding Agreement")
    for row in doc.items:
        targets=grouped.get(row.name,[])
        if targets:split_snapshot(doc,row)

def append_distributed(stage,doc,row,direction,effect,remarks,upstream_doctype=None,upstream_row=None):
    parts=split_snapshot(doc,row);created=[]
    for part in parts:
        target=part["target"];snap=part["snapshot"];bl=_target_value(target,"budget_line",row_budget_line(row));project=_target_value(target,"project",row.get("project") or doc.get("project"))
        if not bl or not project:frappe.throw(f"Budget Line and Project required for source row {row.idx}")
        # existing process or deterministic distributed direct ledger
        process=doc.get("custom_procurement_process")
        source_key=f"DIST|{doc.company}|{project}|{bl}|{doc.doctype}|{doc.name}|{row.name}|{target.name if target else 'BASE'}"
        name=frappe.db.get_value("Commitment Ledger",{"source_key":source_key},"name")
        ledger=frappe.get_doc("Commitment Ledger",name) if name else frappe.new_doc("Commitment Ledger")
        if ledger.is_new():ledger.update({"company":doc.company,"project":project,"budget_line":bl,"currency":doc.currency,"source_key":source_key,"procurement_process":process})
        event=_append(ledger,stage,doc,row,snap["base_amount"],direction,effect,upstream_doctype,upstream_row,remarks,snap)
        if event and target:
            event.cost_distribution_row=target.name;event.cost_distribution_ledger=target.get("cost_distribution_ledger");event.funding_agreement=target.funding_agreement;event.donor=target.donor;event.allocation_percentage=target.allocation_percentage;event.distribution_snapshot=json.dumps({"row":target.name,"project":project,"budget_line":bl,"funding_agreement":target.funding_agreement,"donor":target.donor,"allocated_amount":target.allocated_amount,"base_amount":target.base_amount,"currency":target.currency,"exchange_rate":target.exchange_rate},sort_keys=True,default=str)
        ledger.save(ignore_permissions=True);created.append(ledger.name)
    return created
