import frappe
from frappe.utils import add_days,nowdate
from .notifications import notify_users,_users_for_role
def daily():
    today=nowdate();soon=add_days(today,30)
    for dt,date_field,roles in (("Workforce Funding Plan","effective_to",["Payroll Manager","HR Manager"]),("Payroll Cost Policy","effective_to",["Payroll Manager","Accounts Manager"])):
        if not frappe.db.exists("DocType",dt):continue
        for row in frappe.get_all(dt,filters={"docstatus":1,date_field:["between",[today,soon]]},fields=["name","company",date_field],limit_page_length=0):
            users=[]
            for role in roles:users+=_users_for_role(role,row.company)
            notify_users(f"{dt} expiring",f"{dt} {row.name} expires on {row.get(date_field)}.",dt,row.name,users)
    for run in frappe.get_all("Payroll Allocation Run",filters={"docstatus":1,"status":"Posted","reconciliation_status":["!=","Matched"]},fields=["name","company"],limit_page_length=0):notify_users("Payroll allocation not reconciled",f"Payroll Allocation Run {run.name} remains unreconciled.","Payroll Allocation Run",run.name,_users_for_role("Accounts Manager",run.company))
