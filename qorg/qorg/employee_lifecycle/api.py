import frappe
from qorg.qorg.employee_lifecycle.service import prepare_commencement

@frappe.whitelist()
def prepare_from_commencement(name):
    doc = frappe.get_doc("Work Commencement Notice", name)
    doc.check_permission("write")
    if doc.docstatus != 0:
        frappe.throw("Only a draft Work Commencement Notice can be prepared.")
    result = prepare_commencement(doc)
    doc.save()
    return result

@frappe.whitelist()
def evaluate_readiness(employee):
    from qorg.qorg.employee_lifecycle.activation import evaluate_employee_readiness
    doc = frappe.get_doc("Employee", employee)
    doc.check_permission("read")
    return evaluate_employee_readiness(employee, persist=True).as_dict()

@frappe.whitelist()
def activate_services(employee, services=None, effective_dates=None):
    import json
    from qorg.qorg.employee_lifecycle.activation import activate_ready_services
    parsed_services = json.loads(services) if isinstance(services, str) else services
    parsed_dates = json.loads(effective_dates) if isinstance(effective_dates, str) else effective_dates
    return activate_ready_services(employee, parsed_services, parsed_dates)

@frappe.whitelist()
def source_of_truth_policy(fieldname=None):
    from qorg.qorg.employee_lifecycle.source_of_truth import get_policy
    return get_policy(fieldname)
