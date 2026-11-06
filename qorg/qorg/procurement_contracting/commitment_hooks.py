import frappe
from frappe.utils import flt
from .commitment_engine import record


def _process_from_material_request(name):
    return frappe.db.get_value("Procurement Process", {"material_request": name}, "name")


def material_request_submit(doc, method=None):
    if doc.material_request_type != "Purchase":
        return
    process = doc.get("custom_procurement_process") or _process_from_material_request(doc.name)
    if process:
        record(process, "Requested", doc.doctype, doc.name, doc.get("custom_estimated_procurement_value") or 0)


def purchase_order_submit(doc, method=None):
    process = None
    for row in doc.items:
        if row.material_request:
            process = _process_from_material_request(row.material_request)
            if process:
                break
    if process:
        record(process, "Ordered", doc.doctype, doc.name, doc.grand_total)


def contract_submit(doc, method=None):
    if doc.procurement_process:
        record(doc.procurement_process, "Contracted", doc.doctype, doc.name, doc.contract_value)


def acceptance_submit(doc, method=None):
    if doc.procurement_process and doc.accepted:
        record(doc.procurement_process, "Accepted", doc.doctype, doc.name, doc.accepted_amount)


def invoice_submit(doc, method=None):
    process = None
    for row in doc.items:
        if row.purchase_order:
            process = frappe.db.get_value("Award Decision", {"purchase_order": row.purchase_order, "docstatus": 1}, "procurement_process")
            if process:
                break
    if process:
        record(process, "Invoiced", doc.doctype, doc.name, doc.grand_total)


def payment_submit(doc, method=None):
    for ref in doc.references:
        if ref.reference_doctype != "Purchase Invoice":
            continue
        process = None
        invoice = frappe.get_doc("Purchase Invoice", ref.reference_name)
        for row in invoice.items:
            if row.purchase_order:
                process = frappe.db.get_value("Award Decision", {"purchase_order": row.purchase_order, "docstatus": 1}, "procurement_process")
                if process:
                    break
        if process:
            record(process, "Paid", doc.doctype, doc.name, ref.allocated_amount)

def _reverse(reference_doctype, reference_name, stage, process, amount):
    if process:
        record(process, stage, reference_doctype, reference_name, amount, direction="Decrease", remarks="Automatic reversal on cancellation")


def material_request_cancel(doc, method=None):
    process = doc.get("custom_procurement_process") or _process_from_material_request(doc.name)
    _reverse(doc.doctype, doc.name, "Requested", process, doc.get("custom_estimated_procurement_value") or 0)


def purchase_order_cancel(doc, method=None):
    process = None
    for row in doc.items:
        if row.material_request:
            process = _process_from_material_request(row.material_request)
            if process:
                break
    _reverse(doc.doctype, doc.name, "Ordered", process, doc.grand_total)


def contract_cancel(doc, method=None):
    _reverse(doc.doctype, doc.name, "Contracted", doc.procurement_process, doc.contract_value)


def acceptance_cancel(doc, method=None):
    _reverse(doc.doctype, doc.name, "Accepted", doc.procurement_process, doc.accepted_amount)


def invoice_cancel(doc, method=None):
    process = None
    for row in doc.items:
        if row.purchase_order:
            process = frappe.db.get_value("Award Decision", {"purchase_order": row.purchase_order}, "procurement_process")
            if process:
                break
    _reverse(doc.doctype, doc.name, "Invoiced", process, doc.grand_total)


def payment_cancel(doc, method=None):
    for ref in doc.references:
        if ref.reference_doctype != "Purchase Invoice":
            continue
        invoice = frappe.get_doc("Purchase Invoice", ref.reference_name)
        process = None
        for row in invoice.items:
            if row.purchase_order:
                process = frappe.db.get_value("Award Decision", {"purchase_order": row.purchase_order}, "procurement_process")
                if process:
                    break
        _reverse(doc.doctype, doc.name, "Paid", process, ref.allocated_amount)
