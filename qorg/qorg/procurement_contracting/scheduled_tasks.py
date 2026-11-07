import frappe
from frappe.utils import add_days,nowdate
from qorg.qorg.procurement_contracting.communications import send_template
from qorg.qorg.procurement_contracting.settings import get_setting

def _send_once(key,doctype,name,template,recipients):
 if not recipients:return
 marker=f"qorg-reminder:{key}:{doctype}:{name}:{nowdate()}"
 if frappe.cache().get_value(marker):return
 send_template(doctype,name,template,recipients)
 frappe.cache().set_value(marker,1,expires_in_sec=86400*2)

def send_procurement_reminders():
 if not get_setting("enable_procurement_notifications",1):return
 submission_days=int(get_setting("submission_reminder_days",3) or 3)
 target=add_days(nowdate(),submission_days)
 for row in frappe.get_all("Procurement Notice",filters={"published":1,"docstatus":1,"deadline":["between",[target+" 00:00:00",target+" 23:59:59"]]},fields=["name","owner"]):
  _send_once("submission", "Procurement Notice",row.name,"Submission Deadline Reminder",row.owner)
 contract_days=int(get_setting("contract_expiry_alert_days",30) or 30)
 for row in frappe.get_all("Procurement Contract",filters={"status":"Active","end_date":add_days(nowdate(),contract_days)},fields=["name","contract_manager"]):
  _send_once("contract", "Procurement Contract",row.name,"Contract Expiry Reminder",row.contract_manager)
 # Guarantee and milestone reminders are sent to the contract manager from child rows.
 for c in frappe.get_all("Procurement Contract",filters={"status":"Active"},fields=["name","contract_manager"]):
  doc=frappe.get_doc("Procurement Contract",c.name)
  gdays=int(get_setting("guarantee_expiry_alert_days",30) or 30)
  if any(str(r.valid_to or "")==str(add_days(nowdate(),gdays)) for r in doc.guarantees):_send_once("guarantee",doc.doctype,doc.name,"Guarantee Expiry Reminder",c.contract_manager)
  if any(str(r.due_date or "")==str(add_days(nowdate(),7)) and r.status not in ("Completed","Cancelled") for r in doc.milestones):_send_once("milestone",doc.doctype,doc.name,"Contract Milestone Reminder",c.contract_manager)

# Backward-compatible hook retained for installations upgraded from procurement v1.3.
def daily_procurement_alerts():
    return send_procurement_reminders()
