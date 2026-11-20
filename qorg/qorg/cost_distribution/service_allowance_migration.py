from __future__ import annotations
import json
import frappe
from frappe import _
from frappe.utils import now_datetime
OLD_MAIN="Service and Allowance Accrual";NEW_MAIN="Service Allowance Accrual";OLD_LINE="Service and Allowance Accrual Line";NEW_LINE="Service Allowance Line";REPORT="qorg-service-allowance-name-migration.json"
def migrate_service_allowance_names():
 report={"started_on":str(now_datetime()),"old_main":0,"new_main_before":0,"old_lines":0,"new_lines_before":0,"copied_main":0,"copied_lines":0,"copied_distributions":0,"updated_references":{},"errors":[]}
 if not all(frappe.db.exists("DocType",x) for x in (OLD_MAIN,NEW_MAIN,OLD_LINE,NEW_LINE)):
  report["skipped"]="Required old/new DocTypes are not all present after schema sync.";_write(report);return report
 report["old_main"]=frappe.db.count(OLD_MAIN);report["new_main_before"]=frappe.db.count(NEW_MAIN);report["old_lines"]=frappe.db.count(OLD_LINE);report["new_lines_before"]=frappe.db.count(NEW_LINE)
 try:
  report["copied_main"]=_copy_table(OLD_MAIN,NEW_MAIN);report["copied_lines"]=_copy_table(OLD_LINE,NEW_LINE,parenttype=NEW_MAIN);report["copied_distributions"]=_copy_distribution_rows();report["updated_references"]=_update_known_references();_validate_parity()
 except Exception as exc:report["errors"].append(repr(exc));_write(report);raise
 report.update({"finished_on":str(now_datetime()),"new_main_after":frappe.db.count(NEW_MAIN),"new_lines_after":frappe.db.count(NEW_LINE),"ready_for_acceptance":True});_write(report);return report
def audit_legacy_cleanup_readiness():
 result={"old_main":frappe.db.count(OLD_MAIN) if frappe.db.exists("DocType",OLD_MAIN) else 0,"new_main":frappe.db.count(NEW_MAIN) if frappe.db.exists("DocType",NEW_MAIN) else 0,"old_lines":frappe.db.count(OLD_LINE) if frappe.db.exists("DocType",OLD_LINE) else 0,"new_lines":frappe.db.count(NEW_LINE) if frappe.db.exists("DocType",NEW_LINE) else 0,"blocking_references":_blocking_references(),"checked_on":str(now_datetime())};result["ready"]=(result["old_main"]==result["new_main"] and result["old_lines"]==result["new_lines"] and not result["blocking_references"]);_write_named("qorg-service-allowance-cleanup-readiness.json",result);return result
def _copy_table(old_dt,new_dt,parenttype=None):
 old_cols=set(frappe.db.get_table_columns(old_dt));new_cols=set(frappe.db.get_table_columns(new_dt));cols=sorted(old_cols & new_cols)
 if not cols:return 0
 before=set(frappe.get_all(new_dt,pluck="name",limit_page_length=0));select=[]
 for col in cols:
  if col=="parenttype" and parenttype:select.append(f"{frappe.db.escape(parenttype)} as `parenttype`")
  else:select.append(f"`{col}`")
 frappe.db.sql(f"INSERT IGNORE INTO `tab{new_dt}` ({','.join('`'+x+'`' for x in cols)}) SELECT {','.join(select)} FROM `tab{old_dt}`")
 return len(set(frappe.get_all(new_dt,pluck="name",limit_page_length=0))-before)
def _copy_distribution_rows():
 if not frappe.db.exists("DocType","Cost Distribution Row"):return 0
 count=0
 for row in frappe.get_all("Cost Distribution Row",filters={"parenttype":OLD_MAIN},fields=["*"],limit_page_length=0):
  new_name=f"{row.name}-N"
  if frappe.db.exists("Cost Distribution Row",new_name):continue
  values=dict(row);values.update({"name":new_name,"parenttype":NEW_MAIN,"doctype":"Cost Distribution Row"})
  for key in ("creation","modified","modified_by","owner"):values.pop(key,None)
  frappe.get_doc(values).insert(ignore_permissions=True,set_name=new_name);count+=1
 return count
def _update_known_references():
 counts={}
 for dt,field in (("Journal Entry","custom_qorg_source_doctype"),("Cost Distribution Ledger","source_doctype"),("Cost Distribution Ledger","distribution_document_type"),("Workflow","document_type"),("Report","ref_doctype"),("Print Format","doc_type"),("Notification","document_type")):
  if not frappe.db.exists("DocType",dt) or not frappe.get_meta(dt).has_field(field):continue
  names=frappe.get_all(dt,filters={field:OLD_MAIN},pluck="name",limit_page_length=0)
  for name in names:frappe.db.set_value(dt,name,field,NEW_MAIN,update_modified=False)
  counts[f"{dt}.{field}"]=len(names)
 return counts
def _blocking_references():
 refs=[]
 for dt,field in (("Journal Entry","custom_qorg_source_doctype"),("Cost Distribution Ledger","source_doctype"),("Cost Distribution Ledger","distribution_document_type"),("Workflow","document_type"),("Report","ref_doctype"),("Print Format","doc_type"),("Notification","document_type")):
  if frappe.db.exists("DocType",dt) and frappe.get_meta(dt).has_field(field):
   count=frappe.db.count(dt,{field:OLD_MAIN})
   if count:refs.append({"doctype":dt,"field":field,"count":count})
 return refs
def _validate_parity():
 a,b,c,d=frappe.db.count(OLD_MAIN),frappe.db.count(NEW_MAIN),frappe.db.count(OLD_LINE),frappe.db.count(NEW_LINE)
 if a!=b or c!=d:frappe.throw(_("Service Allowance migration parity failed: main {0}/{1}, lines {2}/{3}").format(a,b,c,d))
def _write(report):_write_named(REPORT,report)
def _write_named(name,report):
 with open(frappe.get_site_path("private","files",name),"w",encoding="utf-8") as handle:json.dump(report,handle,ensure_ascii=False,indent=2,default=str)
