import frappe
from frappe import _

def _enabled(company):
    meta=frappe.get_meta("Company")
    return bool(meta.has_field("custom_enable_payroll_allocation") and frappe.db.get_value("Company",company,"custom_enable_payroll_allocation"))
def _set(doctype,name,values):
    meta=frappe.get_meta(doctype)
    for field,value in values.items():
        if meta.has_field(field): frappe.db.set_value(doctype,name,field,value,update_modified=False)
def validate_payroll_entry(doc,method=None):
    if not _enabled(doc.company): return
    if doc.meta.has_field("custom_payroll_preflight_status") and not doc.custom_payroll_preflight_status: doc.custom_payroll_preflight_status="Not Run"
    if doc.meta.has_field("custom_payroll_allocation_status") and not doc.custom_payroll_allocation_status: doc.custom_payroll_allocation_status="Pending"
def salary_slip_on_submit(doc,method=None):
    _set("Salary Slip",doc.name,{"custom_payroll_allocation_status":"Pending" if _enabled(doc.company) else "Not Required"})
def salary_slip_on_cancel(doc,method=None):
    linked=frappe.db.exists("Payroll Allocation Result",{"salary_slip":doc.name,"parenttype":"Payroll Allocation Run","docstatus":1}) if frappe.db.exists("DocType","Payroll Allocation Result") else None
    if linked: frappe.throw(_("Cancel or reverse the linked Payroll Allocation Run before cancelling this Salary Slip."))
def update_source_status(run,status):
    _set("Payroll Entry",run.payroll_entry,{"custom_payroll_allocation_status":status,"custom_payroll_allocation_run":run.name})
    for slip in frappe.get_all("Salary Slip",filters={"payroll_entry":run.payroll_entry,"docstatus":1},pluck="name"):
        _set("Salary Slip",slip,{"custom_payroll_allocation_status":status,"custom_payroll_allocation_run":run.name})
