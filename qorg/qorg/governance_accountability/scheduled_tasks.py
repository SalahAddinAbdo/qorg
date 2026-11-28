from __future__ import annotations
import frappe
from frappe.utils import now_datetime
OPEN=("Received","Acknowledged","Triaged","Assigned","Under Review","Referred","Under Investigation","Action in Progress","Response Prepared","Response Delivered","Pending Confirmation","Escalated","Appealed","Reopened","Unable to Contact")
def daily_case_sla_and_updates():
    settings=frappe.get_single("Governance and Accountability Settings");now=now_datetime();updated=0;escalated=0
    rows=frappe.get_all("Accountability Case",filters={"status":["in",OPEN]},fields=["name","response_due_on","next_reporter_update_due_on","priority","receiving_role"])
    for row in rows:
        overdue=bool(row.response_due_on and row.response_due_on<now);update_overdue=bool(row.next_reporter_update_due_on and row.next_reporter_update_due_on<now)
        values={"overdue":int(overdue),"reporter_update_overdue":int(update_overdue)}
        if overdue and row.priority=="Critical" and settings.critical_escalation_role:
            values.update({"receiving_role":settings.critical_escalation_role,"status":"Escalated"});escalated+=1
        frappe.db.set_value("Accountability Case",row.name,values,update_modified=False);updated+=1
    return {"ok":True,"updated":updated,"escalated":escalated}
