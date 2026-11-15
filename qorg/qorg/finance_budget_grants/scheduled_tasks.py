from __future__ import annotations
import frappe
from frappe.utils import add_days,getdate,nowdate,date_diff
from frappe.email.doctype.email_template.email_template import get_email_template

def send_funding_reminders():
 today=getdate(nowdate()); horizon=add_days(today,14); sent=[]
 for agreement in frappe.get_all("Funding Agreement",filters={"status":["in",["Active","Closing"]]},pluck="name"):
  doc=frappe.get_doc("Funding Agreement",agreement)
  for row in doc.installments:
   if row.status in ("Received","Cancelled") or not row.due_date: continue
   if getdate(row.due_date)<=horizon:
    _send_once(doc,row,"installment",f"installment:{row.idx}:{row.due_date}"); sent.append(f"{doc.name}:installment:{row.idx}")
  for row in doc.reporting_schedule:
   if row.status in ("Submitted","Accepted") or not row.due_date: continue
   if getdate(row.due_date)<=horizon:
    _send_once(doc,row,"report",f"report:{row.idx}:{row.due_date}"); sent.append(f"{doc.name}:report:{row.idx}")
 return sent

def _send_once(doc,row,obligation_type,key):
 template="Funding Obligation Reminder"; reference=f"{template}:{key}"
 if frappe.db.exists("Communication",{"reference_doctype":doc.doctype,"reference_name":doc.name,"subject":["like",f"%{reference}%"]}): return
 recipients=_recipients(doc,row)
 if not recipients: return
 context=doc.as_dict(); context.update({"obligation_type":obligation_type,"obligation_title":row.get("installment_title") or row.get("report_type"),"obligation_amount":row.get("amount"),"obligation_due_date":row.get("due_date"),"days_overdue":max(date_diff(nowdate(),row.get("due_date")),0)})
 data=get_email_template(template,context); subject=f"{data.get('subject')} [{reference}]"
 frappe.sendmail(recipients=recipients,subject=subject,message=data.get("message"),reference_doctype=doc.doctype,reference_name=doc.name)

def _recipients(doc,row=None):
 candidates=[]
 if row and row.get("responsible_user"): candidates.append(row.responsible_user)
 if doc.meta.has_field("custom_current_responsible_user") and doc.get("custom_current_responsible_user"): candidates.append(doc.custom_current_responsible_user)
 if doc.get("project") and frappe.get_meta("Project").has_field("project_manager"):
  manager=frappe.db.get_value("Project",doc.project,"project_manager")
  if manager: candidates.append(manager)
 return sorted({u for u in candidates if u and frappe.db.get_value("User",u,"enabled")})
