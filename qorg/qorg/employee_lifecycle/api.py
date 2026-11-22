import json
import frappe

@frappe.whitelist()
def prepare_from_commencement(name):
    from qorg.qorg.employee_lifecycle.service import prepare_commencement
    doc=frappe.get_doc("Work Commencement Notice",name);doc.check_permission("write")
    if doc.docstatus!=0:frappe.throw("Only a draft Work Commencement Notice can be prepared.")
    result=prepare_commencement(doc);doc.save();return result

@frappe.whitelist()
def evaluate_readiness(employee):
    from qorg.qorg.employee_lifecycle.documents import evaluate_readiness_with_documents
    frappe.get_doc("Employee",employee).check_permission("read")
    return evaluate_readiness_with_documents(employee,persist=True).as_dict()

@frappe.whitelist()
def activate_services(employee,services=None,effective_dates=None):
    from qorg.qorg.employee_lifecycle.documents import evaluate_readiness_with_documents
    from qorg.qorg.employee_lifecycle.activation import activate_ready_services
    parsed=json.loads(services) if isinstance(services,str) else services
    dates=json.loads(effective_dates) if isinstance(effective_dates,str) else effective_dates
    result=evaluate_readiness_with_documents(employee,persist=True)
    blocked={s:result.services[s].blockers for s in (parsed or result.services) if not result.services[s].ready}
    if blocked:frappe.throw("Services are blocked: "+json.dumps(blocked,ensure_ascii=False))
    return activate_ready_services(employee,parsed,dates)

@frappe.whitelist()
def source_of_truth_policy(fieldname=None):
    from qorg.qorg.employee_lifecycle.source_of_truth import get_policy
    return get_policy(fieldname)

@frappe.whitelist()
def movement_timeline(employee):
    from qorg.qorg.employee_lifecycle.movements import employee_movement_timeline
    frappe.get_doc("Employee",employee).check_permission("read")
    return employee_movement_timeline(employee)

@frappe.whitelist()
def employee_document_compliance(employee):
    from qorg.qorg.employee_lifecycle.documents import document_compliance
    frappe.get_doc("Employee",employee).check_permission("read")
    return document_compliance("Employee",employee)
