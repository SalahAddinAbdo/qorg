import frappe
from frappe import _
from frappe.utils import today,date_diff,flt
VIEWS={
"Executive":["employee","employee_name","name","company","custom_last_working_date","overall_status","custom_completion_percentage","custom_blocked_items","days_overdue"],
"HR":["employee","employee_name","name","company","branch","department","designation","custom_last_working_date","overall_status","custom_document_clearance_status","custom_contract_clearance_status"],
"Finance and Payroll":["employee","employee_name","name","company","custom_financial_clearance_status","custom_payroll_clearance_status","custom_total_outstanding_amount","currency","days_overdue"],
"Assets and Stock":["employee","employee_name","name","company","custom_asset_clearance_status","custom_stock_clearance_status","custom_blocked_items","days_overdue"],
"IT and Access":["employee","employee_name","name","company","custom_user_id","custom_system_access_status","custom_access_closed_on","custom_responsibilities_transferred","custom_handover_to_user"],
"Full":None}
def _dt():return "Employee Separation" if frappe.db.exists("DocType","Employee Separation") else "Employee Offboarding" if frappe.db.exists("DocType","Employee Offboarding") else None
def _multi(v):return v if isinstance(v,list) else [x.strip() for x in (v or "").split(",") if x.strip()]
def execute(filters=None):
 f=frappe._dict(filters or {});dt=_dt()
 if not dt:return [],[],_("Employee Separation is not available."),None,[],1
 meta=frappe.get_meta(dt);db={}
 for key,src in (("company","companies"),("branch","branches"),("department","departments"),("designation","designations"),("employee","employees"),("custom_overall_clearance_status","clearance_statuses")):
  vals=_multi(f.get(src));
  if vals and meta.has_field(key):db[key]=["in",vals]
 if f.last_working_date_from and meta.has_field("custom_last_working_date"):db.setdefault("custom_last_working_date",["between",[f.last_working_date_from,f.last_working_date_to or today()]])
 source=["name","employee"]+[x for x in ["employee_name","company","branch","department","designation","custom_last_working_date","custom_overall_clearance_status","custom_completion_percentage","custom_required_items","custom_completed_items","custom_blocked_items","custom_total_outstanding_amount","custom_financial_clearance_status","custom_payroll_clearance_status","custom_asset_clearance_status","custom_stock_clearance_status","custom_contract_clearance_status","custom_document_clearance_status","custom_system_access_status","custom_access_closed_on","custom_responsibilities_transferred","custom_handover_to_user","custom_user_id","custom_reopened"] if meta.has_field(x)]
 data=frappe.get_all(dt,fields=source,filters=db,limit_page_length=0)
 out=[]
 for r in data:
  r.overall_status=r.get("custom_overall_clearance_status") or "Not Started";d=r.get("custom_last_working_date");r.days_overdue=max(date_diff(today(),d),0) if d else 0;r.currency=None
  if f.overdue_only and not r.days_overdue:continue
  if f.has_outstanding and not flt(r.get("custom_total_outstanding_amount")):continue
  if f.reopened_only and not r.get("custom_reopened"):continue
  r._priority={"Blocked":0,"Ready for Approval":2,"In Progress":3,"Not Started":4,"Completed":5,"Reopened":1}.get(r.overall_status,6);out.append(r)
 out.sort(key=lambda x:(x._priority,-x.days_overdue,x.get("employee_name") or ""))
 defs={"employee":(_("Employee"),"Link","Employee",150,1),"employee_name":(_("Employee Name"),"Data",None,180,1),"name":(_("Separation"),"Link",dt,160,0),"company":(_("Company"),"Link","Company",140,0),"branch":(_("Branch"),"Link","Branch",120,0),"department":(_("Department"),"Link","Department",140,0),"designation":(_("Designation"),"Link","Designation",130,0),"custom_last_working_date":(_("Last Working Date"),"Date",None,120,0),"overall_status":(_("Overall Status"),"Data",None,135,0),"custom_completion_percentage":(_("Completion %"),"Percent",None,105,0),"custom_required_items":(_("Required"),"Int",None,80,0),"custom_completed_items":(_("Completed"),"Int",None,85,0),"custom_blocked_items":(_("Blocked"),"Int",None,80,0),"custom_total_outstanding_amount":(_("Outstanding"),"Currency","currency",120,0),"currency":(_("Currency"),"Link","Currency",90,0),"days_overdue":(_("Days Overdue"),"Int",None,95,0),"custom_financial_clearance_status":(_("Financial"),"Data",None,110,0),"custom_payroll_clearance_status":(_("Payroll"),"Data",None,110,0),"custom_asset_clearance_status":(_("Assets"),"Data",None,110,0),"custom_stock_clearance_status":(_("Stock"),"Data",None,110,0),"custom_contract_clearance_status":(_("Contract"),"Data",None,110,0),"custom_document_clearance_status":(_("Documents"),"Data",None,110,0),"custom_system_access_status":(_("Access"),"Data",None,110,0),"custom_access_closed_on":(_("Access Closed On"),"Datetime",None,145,0),"custom_responsibilities_transferred":(_("Transferred"),"Check",None,95,0),"custom_handover_to_user":(_("Handover User"),"Link","User",150,0),"custom_user_id":(_("Departing User"),"Link","User",150,0)}
 keys=VIEWS.get(f.view or "Executive") or list(defs)
 cols=[]
 for k in keys:
  label,typ,opt,width,sticky=defs[k];c={"label":label,"fieldname":k,"fieldtype":typ,"width":width,"sticky":bool(sticky)}
  if opt:c["options"]=opt
  cols.append(c)
 counts={};
 for r in out:counts[r.overall_status]=counts.get(r.overall_status,0)+1
 summary=[{"value":len(out),"indicator":"Blue","label":_("Total Separations"),"datatype":"Int"},{"value":counts.get("Completed",0),"indicator":"Green","label":_("Completed"),"datatype":"Int"},{"value":counts.get("Blocked",0),"indicator":"Red","label":_("Blocked"),"datatype":"Int"},{"value":sum(1 for r in out if r.days_overdue),"indicator":"Orange","label":_("Overdue"),"datatype":"Int"},{"value":sum(1 for r in out if r.get("custom_system_access_status")=="Pending Closure"),"indicator":"Red","label":_("Pending Access Closure"),"datatype":"Int"}]
 view=f.view or "Executive";chart={"data":{"labels":list(counts),"datasets":[{"name":_("Separations"),"values":list(counts.values())}]},"type":"donut","height":260}
 return cols,out,None,chart,summary,1
