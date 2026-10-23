import frappe
from frappe.desk.query_report import get_report_doc as core_get_report_doc, run as core_run
from qorg.qorg.enterprise_foundation.interface_policy_engine import get_interface_policy
def _check(name):
 if name and frappe.session.user!="Administrator" and get_interface_policy("Report",name) in {"Restricted","Disabled","Deprecated"}: frappe.throw(f"Report {name} is not available.",frappe.PermissionError)
def get_report_doc(report_name,*args,**kwargs): _check(report_name); return core_get_report_doc(report_name,*args,**kwargs)
def run(report_name,*args,**kwargs): _check(report_name); return core_run(report_name,*args,**kwargs)
