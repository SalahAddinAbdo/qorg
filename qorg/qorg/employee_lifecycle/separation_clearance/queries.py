from __future__ import annotations
import frappe
@frappe.whitelist()
def employee_query(doctype,txt,searchfield,start,page_len,filters):
 f={"status":"Active"};company=(filters or {}).get("company");exclude=(filters or {}).get("exclude_employee")
 if company:f["company"]=company
 rows=frappe.get_all("Employee",filters=f,or_filters={"name":["like",f"%{txt}%"],"employee_name":["like",f"%{txt}%"]},fields=["name","employee_name","department","designation"],start=start,page_length=page_len,order_by="employee_name")
 return [(r.name,r.employee_name,r.department or "",r.designation or "") for r in rows if r.name!=exclude]
@frappe.whitelist()
def active_user_query(doctype,txt,searchfield,start,page_len,filters):
 role=(filters or {}).get("role");users=None
 if role:users=set(frappe.get_all("Has Role",filters={"role":role,"parenttype":"User"},pluck="parent"))
 rows=frappe.get_all("User",filters={"enabled":1,"user_type":"System User","name":["not in",["Administrator","Guest"]]},or_filters={"name":["like",f"%{txt}%"],"full_name":["like",f"%{txt}%"]},fields=["name","full_name"],start=start,page_length=page_len,order_by="full_name")
 return [(r.name,r.full_name) for r in rows if users is None or r.name in users]
@frappe.whitelist()
def contract_query(doctype,txt,searchfield,start,page_len,filters):
 meta=frappe.get_meta("Contract");f={"docstatus":["<",2]};employee=(filters or {}).get("employee");company=(filters or {}).get("company")
 for fld in ("custom_employee","employee"):
  if employee and meta.has_field(fld):f[fld]=employee;break
 if company and meta.has_field("company"):f["company"]=company
 return frappe.db.get_values("Contract",filters=f,fieldname=["name","party_name","status"],as_list=True,limit_start=start,limit_page_length=page_len,order_by="modified desc")
@frappe.whitelist()
def related_record_query(doctype,txt,searchfield,start,page_len,filters):
 employee=(filters or {}).get("employee");company=(filters or {}).get("company");meta=frappe.get_meta(doctype);f={"docstatus":["<",2]}
 if employee and meta.has_field("employee"):f["employee"]=employee
 if company and meta.has_field("company"):f["company"]=company
 return frappe.db.get_values(doctype,filters=f,fieldname=["name"],as_list=True,limit_start=start,limit_page_length=page_len,order_by="modified desc")
