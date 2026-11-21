import frappe
from qorg.qorg.payroll_workforce_allocation.readiness import evaluate_payroll_entry
from qorg.qorg.payroll_workforce_allocation.reporting import assert_report_access,summary,col
def execute(filters=None):
 assert_report_access();f=frappe._dict(filters or {});where={}
 if f.get("company"):where["company"]=f.company
 if f.get("from_date"):where["start_date"]=[">=",f.from_date]
 if f.get("to_date"):where["end_date"]=["<=",f.to_date]
 rows=[]
 for name in frappe.get_all("Payroll Entry",filters=where,pluck="name",order_by="modified desc",limit_page_length=0):
  r=evaluate_payroll_entry(name)
  if f.get("status") and r["status"]!=f.status:continue
  rows.append({**r,"blocker_count":sum(x["severity"]=="Blocker" for x in r["issues"]),"warning_count":sum(x["severity"]=="Warning" for x in r["issues"])})
 cols=[col("payroll_entry","Payroll Entry","Link","Payroll Entry",180,True),col("company","Company","Link","Company",160,True),col("status","Readiness","Data",width=110),col("salary_slip_count","Salary Slips","Int",width=100),col("blocker_count","Blockers","Int",width=90),col("warning_count","Warnings","Int",width=90)];cards=[summary(len(rows),"Payroll Entries","Int"),summary(sum(x["status"]=="Passed" for x in rows),"Ready","Int","Green"),summary(sum(x["status"]=="Blocked" for x in rows),"Blocked","Int","Red")];chart={"data":{"labels":["Passed","Warnings","Blocked"],"datasets":[{"values":[sum(x["status"]==s for x in rows) for s in ("Passed","Warnings","Blocked")]}]},"type":"donut"};return cols,rows,None,chart,cards
