from __future__ import annotations
import frappe
REFERENCE_FIELDS=(
 ("Purchase Invoice Item","po_detail","Purchase Order Item"),("Purchase Invoice Item","pr_detail","Purchase Receipt Item"),
 ("Purchase Order Item","material_request_item","Material Request Item"),("Purchase Order Item","supplier_quotation_item","Supplier Quotation Item"),
 ("Supplier Quotation Item","material_request_item","Material Request Item"),("Stock Entry Detail","material_request_item","Material Request Item"),
)
def ensure_source_key(row):
 if not row.get("custom_distribution_source_key"):
  for child,field,source_dt in REFERENCE_FIELDS:
   if row.doctype==child and row.get(field):
    key=frappe.db.get_value(source_dt,row.get(field),"custom_distribution_source_key")
    if key:row.custom_distribution_source_key=key;return key
  row.custom_distribution_source_key=frappe.generate_hash(length=20)
 return row.custom_distribution_source_key
def inherited_rows(doc,source_key):
 result=[]
 for source_dt in ("Material Request","Supplier Quotation","Purchase Order","Purchase Receipt","Purchase Invoice"):
  if not frappe.db.exists("DocType",source_dt) or not frappe.get_meta(source_dt).has_field("custom_cost_distributions"):continue
  names=frappe.get_all("Cost Distribution Row",filters={"parenttype":source_dt,"source_key":source_key},pluck="name",limit_page_length=0)
  if names:
   result=[frappe.get_doc("Cost Distribution Row",x) for x in names];break
 return result
