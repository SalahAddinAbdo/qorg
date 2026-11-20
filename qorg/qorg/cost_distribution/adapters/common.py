from __future__ import annotations
import json,frappe
from qorg.qorg.cost_distribution.resolver import resolve_profile
from qorg.qorg.cost_distribution.calculations import calculate_targets
from qorg.qorg.cost_distribution.validation import validate_distribution_rows
from qorg.qorg.cost_distribution.lifecycle import write_ledger,cancel_ledger,source_hash
from qorg.qorg.cost_distribution.inheritance import ensure_source_key,inherited_rows
SOURCE_TABLES={"Material Request":"items","Supplier Quotation":"items","Purchase Order":"items","Purchase Invoice":"items","Expense Claim":"expenses","Stock Entry":"items","Service and Allowance Accrual":"lines"}
def before_validate(doc,method=None):
 table=SOURCE_TABLES.get(doc.doctype);field="cost_distributions" if doc.doctype=="Service and Allowance Accrual" else "custom_cost_distributions"
 if not table or not doc.meta.has_field(field):return
 source_rows=doc.get(table) or []
 for row in source_rows:ensure_source_key(row)
 manual=[r.as_dict(no_nulls=True) for r in doc.get(field) or [] if r.distribution_source in ("Manually Selected","Manually Adjusted")]
 doc.set(field,[])
 for values in manual:
  for k in ("name","idx","parent","parenttype","parentfield","doctype"):values.pop(k,None)
  doc.append(field,values)
 manual_keys={r.source_key for r in doc.get(field)}
 for row in source_rows:
  key=row.custom_distribution_source_key
  if key in manual_keys:continue
  inherited=inherited_rows(doc,key)
  if inherited:
   _append_from_existing(doc,field,row,key,inherited,"Transferred");continue
  profile=resolve_profile(company=doc.company,posting_date=doc.get("posting_date") or doc.get("transaction_date") or frappe.utils.today(),doctype=doc.doctype,item=row.get("item_code"),item_group=frappe.db.get_value("Item",row.get("item_code"),"item_group") if row.get("item_code") else None,expense_type=row.get("expense_type"),expense_account=row.get("expense_account"),department=doc.get("department"),cost_center=row.get("cost_center"),subtype=doc.get("purpose"))
  if not profile or not profile.auto_apply:continue
  amount=row.get("net_amount") or row.get("amount") or row.get("base_amount") or 0;base=row.get("base_net_amount") or row.get("base_amount") or amount
  _append_calc(doc,field,row,key,profile,amount,base)
 sources={r.custom_distribution_source_key:r for r in source_rows};validate_distribution_rows(doc,field,sources,require_all=False)
 doc.custom_distribution_status="Manually Adjusted" if manual else ("Auto Applied" if doc.get(field) else "Not Required")
 if doc.meta.has_field("custom_distribution_hash"):doc.custom_distribution_hash=source_hash(doc,field)
def _base(doc,row,key,source):
 return {"source_doctype":doc.doctype,"source_child_doctype":row.doctype,"source_row":row.name,"source_key":key,"source_row_idx":row.idx,"source_item":row.get("item_code"),"source_account":row.get("expense_account"),"source_description":row.get("description"),"source_quantity":row.get("qty") or 1,"source_amount":row.get("net_amount") or row.get("amount") or 0,"source_base_amount":row.get("base_net_amount") or row.get("base_amount") or 0,"source_snapshot":json.dumps(row.as_dict(no_nulls=True),default=str),"distribution_source":source}
def _append_calc(doc,field,row,key,profile,amount,base):
 for result in calculate_targets(profile,amount,base):
  t=result["target"];values=_base(doc,row,key,"Auto Applied");values.update({"allocation_profile":profile.name,"profile_version":profile.version,"project":t.project,"cost_center":t.cost_center,"department":t.department,"budget_line":t.budget_line,"funding_agreement":t.funding_agreement,"donor":t.donor,"allocation_percentage":t.allocation_percentage,"allocated_amount":result["allocated_amount"],"base_amount":result["base_amount"],"currency":doc.get("currency"),"exchange_rate":doc.get("conversion_rate") or 1,"effective_date":doc.get("posting_date") or doc.get("transaction_date"),"eligibility_status":"Eligible"});doc.append(field,values)
def _append_from_existing(doc,field,row,key,inherited,source):
 total=sum(float(x.allocated_amount or 0) for x in inherited);amount=float(row.get("net_amount") or row.get("amount") or 0);base=float(row.get("base_net_amount") or row.get("base_amount") or amount);used=0.0;base_used=0.0
 for idx,old in enumerate(inherited):
  ratio=float(old.allocated_amount or 0)/total if total else float(old.allocation_percentage or 0)/100
  allocated=round(amount*ratio,2) if idx<len(inherited)-1 else round(amount-used,2);base_allocated=round(base*ratio,2) if idx<len(inherited)-1 else round(base-base_used,2);used+=allocated;base_used+=base_allocated
  values=_base(doc,row,key,source);values.update({"upstream_source_doctype":old.parenttype,"upstream_source_document":old.parent,"upstream_source_row":old.source_row,"allocation_profile":old.allocation_profile,"profile_version":old.profile_version,"project":old.project,"cost_center":old.cost_center,"department":old.department,"budget_line":old.budget_line,"funding_agreement":old.funding_agreement,"donor":old.donor,"allocation_percentage":round(ratio*100,6),"allocated_amount":allocated,"base_amount":base_allocated,"eligibility_status":"Eligible"});doc.append(field,values)
def before_submit(doc,method=None):
 table=SOURCE_TABLES.get(doc.doctype);field="cost_distributions" if doc.doctype=="Service and Allowance Accrual" else "custom_cost_distributions"
 if table and doc.meta.has_field(field):validate_distribution_rows(doc,field,{r.custom_distribution_source_key:r for r in doc.get(table) or []},require_all=False)
def on_submit(doc,method=None):
 field="cost_distributions" if doc.doctype=="Service and Allowance Accrual" else "custom_cost_distributions"
 if doc.meta.has_field(field) and doc.get(field):write_ledger(doc,field)
def on_cancel(doc,method=None):cancel_ledger(doc)
