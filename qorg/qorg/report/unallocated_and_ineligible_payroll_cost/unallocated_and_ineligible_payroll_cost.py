import frappe
from frappe.utils import flt
from qorg.qorg.payroll_workforce_allocation.reporting import assert_report_access,run_names,summary,col
def execute(filters=None):
 assert_report_access();f=frappe._dict(filters or {});runs=run_names(f);where={"parenttype":"Payroll Allocation Run","parent":["in",runs],"resolved":0}
 if f.get("severity"):where["severity"]=f.severity
 if f.get("exception_type"):where["exception_type"]=f.exception_type
 rows=frappe.get_all("Payroll Allocation Exception",filters=where,fields=["parent as allocation_run","employee","salary_slip","salary_component","exception_type","severity","amount","required_action"],limit_page_length=0);cols=[col("allocation_run","Allocation Run","Link","Payroll Allocation Run",170,True),col("employee","Employee","Link","Employee",150,True),col("salary_slip","Salary Slip","Link","Salary Slip",160),col("salary_component","Salary Component","Link","Salary Component",160),col("exception_type","Exception Type","Data",width=150),col("severity","Severity","Data",width=100),col("amount","Amount","Currency",width=120),col("required_action","Required Action","Small Text",width=240)];cards=[summary(len(rows),"Open Exceptions","Int","Red"),summary(sum(flt(x.amount) for x in rows),"Affected Amount")];by={}
 for x in rows:by[x.exception_type]=by.get(x.exception_type,0)+1
 chart={"data":{"labels":list(by),"datasets":[{"values":list(by.values())}]},"type":"donut"};return cols,rows,None,chart,cards
