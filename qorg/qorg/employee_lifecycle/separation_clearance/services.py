from __future__ import annotations
import json,frappe
from frappe import _
from frappe.utils import now_datetime,today,getdate,date_diff
CLOSED={"Completed","Paid","Settled","Approved","Exit Confirmed","Employee Retained","Cancelled"}
def _meta(dt):return frappe.get_meta(dt) if frappe.db.exists("DocType",dt) else None
def _exists(dt,filters):
 try:return frappe.db.exists(dt,filters) if _meta(dt) else None
 except Exception:return None
def _rows(dt,employee):
 m=_meta(dt)
 if not m or not m.has_field("employee"):return []
 fs=["name","docstatus"]+(["status"] if m.has_field("status") else [])
 return frappe.get_all(dt,filters={"employee":employee,"docstatus":["<",2]},fields=fs,limit_page_length=0)
def _open(dt,employee):
 for r in _rows(dt,employee):
  if r.get("status") not in CLOSED:return r.name
 return None
def _complete(dt,employee):return any(r.docstatus==1 or r.get("status") in CLOSED for r in _rows(dt,employee))
def state(employee,req_exit=True,req_ffs=True):
 emp=frappe.get_doc("Employee",employee);user=emp.user_id
 return {"advance":_open("Employee Advance",employee),"expense":_open("Expense Claim",employee),"benefit":_open("Employee Benefit Claim",employee),"salary":_exists("Salary Slip",{"employee":employee,"docstatus":0}),"ffs":_open("Full and Final Statement",employee),"ffs_missing":bool(req_ffs and _meta("Full and Final Statement") and not _complete("Full and Final Statement",employee)),"exit":_open("Exit Interview",employee),"exit_missing":bool(req_exit and _meta("Exit Interview") and not _complete("Exit Interview",employee)),"custody":_exists("Asset Custody",{"custodian":employee,"docstatus":["<",2],"custody_status":["in",["Pending Handover","Active","Return Due","Overdue"]]}),"stock":_exists("Stock Handover",{"recipient_employee":employee,"docstatus":["<",2],"handover_status":["in",["Draft","Pending Handover","Discrepancy Review"]]}),"contract":_exists("Contract",{"custom_employee":employee,"docstatus":["<",2]}) if _meta("Contract") and _meta("Contract").has_field("custom_employee") else None,"documents":_exists("Employee Document Record",{"employee":employee,"docstatus":["<",2]}) if _meta("Employee Document Record") and _meta("Employee Document Record").has_field("employee") else None,"user":user if user and frappe.db.get_value("User",user,"enabled") else None}
def _sync_dates(doc):
 if not doc.meta.has_field("custom_last_working_date"):return
 for f in ("boarding_begins_on","relieving_date","last_working_date"):
  if doc.meta.has_field(f) and doc.get(f):doc.custom_last_working_date=doc.get(f);break
def refresh(doc):
 _sync_dates(doc);s=state(doc.employee,bool(doc.get("custom_exit_interview_required")),bool(doc.get("custom_final_settlement_required")))
 items=doc.get("custom_clearance_items") or [];required=[r for r in items if r.required];completed=[r for r in required if r.status in ("Completed","Exception Approved")];blocked=[r for r in required if r.status=="Blocked"]
 total=sum(float(r.outstanding_amount or 0) for r in items);pct=(len(completed)*100/len(required)) if required else 0
 values={"custom_financial_clearance_status":"Pending" if s["advance"] or s["expense"] or s["benefit"] else "Clear","custom_payroll_clearance_status":"Pending" if s["salary"] or s["ffs"] or s["ffs_missing"] else "Clear","custom_asset_clearance_status":"Pending" if s["custody"] else "Clear","custom_stock_clearance_status":"Pending" if s["stock"] else "Clear","custom_contract_clearance_status":"Pending" if s["contract"] else "Clear","custom_document_clearance_status":"Pending" if s["exit"] or s["exit_missing"] or s["documents"] else "Clear","custom_system_access_status":"Pending Closure" if s["user"] else "Closed","custom_required_items":len(required),"custom_completed_items":len(completed),"custom_blocked_items":len(blocked),"custom_completion_percentage":pct,"custom_total_outstanding_amount":total}
 pending=any(v in ("Pending","Pending Closure") for v in values.values()) or len(completed)<len(required)
 values["custom_overall_clearance_status"]="Blocked" if pending else "Ready for Approval"
 for k,v in values.items():
  if doc.meta.has_field(k):doc.set(k,v)
 if doc.meta.has_field("custom_clearance_snapshot"):doc.custom_clearance_snapshot=json.dumps({"generated_on":str(now_datetime()),"state":s,"metrics":{"required":len(required),"completed":len(completed),"blocked":len(blocked),"percentage":pct,"outstanding":total}},default=str,indent=2)
 return s
def validate_employee_clearance(doc,method=None):
 if not doc.get("employee"):return
 s=refresh(doc)
 if doc.get("custom_handover_to_employee")==doc.employee:frappe.throw(_("Handover employee cannot be the departing employee."))
 closing=doc.docstatus==1 or doc.get("boarding_status") in ("Completed","Complete") or doc.get("status") in ("Completed","Closed")
 if closing:
  blockers=[k for k,v in s.items() if v];blockers += [r.clearance_area for r in (doc.get("custom_clearance_items") or []) if r.required and r.status not in ("Completed","Exception Approved")]
  if blockers:frappe.throw(_("Employee clearance cannot be completed. Outstanding: {0}").format(", ".join(blockers)))
  doc.custom_overall_clearance_status="Completed";doc.custom_clearance_completed_on=now_datetime();doc.custom_clearance_completed_by=frappe.session.user
@frappe.whitelist()
def refresh_employee_clearance(doctype,name):
 doc=frappe.get_doc(doctype,name);doc.check_permission("write");s=refresh(doc);doc.save();return s
@frappe.whitelist()
def populate_default_clearance_items(doctype,name):
 doc=frappe.get_doc(doctype,name);doc.check_permission("write");existing={r.clearance_area for r in doc.get("custom_clearance_items") or []}
 for area,role in [("HR and Documents","HR Manager"),("Supervisor Handover","Projects Manager"),("Finance and Advances","Accounts Manager"),("Payroll and Final Settlement","Payroll Manager"),("Assets and Custody","Asset Manager"),("Stock and Materials","Stock Manager"),("System Access","System Manager"),("Contract Closeout","HR Manager")]:
  if area not in existing:doc.append("custom_clearance_items",{"clearance_area":area,"responsible_role":role,"required":1,"status":"Pending"})
 doc.save();return len(doc.custom_clearance_items)

@frappe.whitelist()
def create_exit_interview(doctype,name):
 doc=frappe.get_doc(doctype,name);doc.check_permission("write");existing=_exists("Exit Interview",{"employee":doc.employee,"docstatus":["<",2]})
 if existing:return existing
 target=frappe.new_doc("Exit Interview");target.employee=doc.employee;target.insert();doc.custom_exit_interview=target.name;doc.save();return target.name
@frappe.whitelist()
def create_full_and_final_statement(doctype,name):
 doc=frappe.get_doc(doctype,name);doc.check_permission("write");existing=_exists("Full and Final Statement",{"employee":doc.employee,"docstatus":["<",2]})
 if existing:return existing
 target=frappe.new_doc("Full and Final Statement");target.employee=doc.employee
 if target.meta.has_field("company"):target.company=doc.get("company") or doc.get("custom_company")
 if target.meta.has_field("transaction_date"):target.transaction_date=today()
 target.insert();doc.custom_full_and_final_statement=target.name;doc.save();return target.name
@frappe.whitelist()
def close_employee_access(doctype,name):
 doc=frappe.get_doc(doctype,name);doc.check_permission("write");user=frappe.db.get_value("Employee",doc.employee,"user_id")
 if user in (None,"Administrator","Guest",frappe.session.user):frappe.throw(_("The linked user cannot be disabled by this action."))
 if not {"System Manager","HR Manager","HR User"}.intersection(frappe.get_roles()):frappe.throw(_("Not permitted."),frappe.PermissionError)
 frappe.db.set_value("User",user,{"enabled":0,"api_key":None,"api_secret":None});frappe.db.delete("Sessions",{"user":user});frappe.clear_cache(user=user);doc.custom_access_closed_on=now_datetime();doc.custom_system_access_status="Closed";doc.save();return user
@frappe.whitelist()
def transfer_open_responsibilities(doctype,name):
 doc=frappe.get_doc(doctype,name);doc.check_permission("write");source=doc.get("custom_user_id");target=doc.get("custom_handover_to_user")
 if not source or not target or source==target:frappe.throw(_("Valid different source and target users are required."))
 todos=frappe.get_all("ToDo",filters={"allocated_to":source,"status":"Open"},pluck="name",limit_page_length=0)
 for n in todos:frappe.db.set_value("ToDo",n,"allocated_to",target)
 for dt in frappe.get_all("Custom Field",filters={"fieldname":"custom_current_responsible_user"},pluck="dt",limit_page_length=0):
  if not frappe.db.exists("DocType",dt):continue
  meta=frappe.get_meta(dt);names=frappe.get_all(dt,filters={"custom_current_responsible_user":source},pluck="name",limit_page_length=0)
  for n in names:
   vals={"custom_current_responsible_user":target}
   if meta.has_field("custom_previous_responsible_user"):vals["custom_previous_responsible_user"]=source
   frappe.db.set_value(dt,n,vals)
 doc.custom_responsibilities_transferred=1;doc.save();return len(todos)
