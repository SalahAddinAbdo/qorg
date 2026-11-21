import frappe
from frappe import _
from .readiness import evaluate_payroll_entry
@frappe.whitelist()
def run_preflight(payroll_entry):
    frappe.get_doc("Payroll Entry",payroll_entry).check_permission("read")
    return evaluate_payroll_entry(payroll_entry)
def assert_preflight(payroll_entry):
    result=evaluate_payroll_entry(payroll_entry)
    if result["status"]=="Blocked": frappe.throw(_("Payroll preflight is blocked. Resolve all blocking issues before allocation."))
    return result
