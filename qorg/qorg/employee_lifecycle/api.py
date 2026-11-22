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
