import hashlib,json,frappe
from frappe.utils import flt
def source_hash(doc,field="custom_cost_distributions"):
 payload=[{k:r.get(k) for k in ("source_key","allocation_profile","profile_version","project","cost_center","budget_line","funding_agreement","donor","department","allocation_percentage","allocated_amount","base_amount")} for r in doc.get(field) or []]
 return hashlib.sha256(json.dumps(payload,sort_keys=True,default=str).encode()).hexdigest()
def write_ledger(doc,field="custom_cost_distributions",mode="Direct"):
 grouped={}
 for row in doc.get(field) or []:grouped.setdefault(row.source_key,[]).append(row)
 for key,rows in grouped.items():
  detail=rows[0].source_row;gl=frappe.db.get_value("GL Entry",{"voucher_type":doc.doctype,"voucher_no":doc.name,"voucher_detail_no":detail,"is_cancelled":0},"name",order_by="creation asc") if frappe.db.exists("DocType","GL Entry") else None
  digest=hashlib.sha256(f"{doc.doctype}|{doc.name}|{key}|{source_hash(doc,field)}".encode()).hexdigest();amount=sum(flt(x.allocated_amount) for x in rows)
  values={"company":doc.company,"source_doctype":doc.doctype,"source_document":doc.name,"source_child_doctype":rows[0].source_child_doctype,"source_row":detail,"source_gl_entry":gl,"source_hash":digest,"original_amount":amount,"distributed_amount":amount,"remaining_amount":0,"status":"Active","allocation_mode":mode,"allocation_profile":rows[0].allocation_profile,"profile_version":rows[0].profile_version,"distribution_document_type":doc.doctype,"distribution_document":doc.name,"target_snapshot":json.dumps([x.as_dict(no_nulls=True) for x in rows],default=str)}
  existing=frappe.db.get_value("Cost Distribution Ledger",{"source_hash":digest},"name")
  if existing:frappe.db.set_value("Cost Distribution Ledger",existing,values,update_modified=False)
  else:frappe.get_doc({"doctype":"Cost Distribution Ledger",**values}).insert(ignore_permissions=True)
def cancel_ledger(doc):
 for n in frappe.get_all("Cost Distribution Ledger",filters={"source_doctype":doc.doctype,"source_document":doc.name,"status":"Active"},pluck="name"):frappe.db.set_value("Cost Distribution Ledger",n,"status","Cancelled",update_modified=False)
