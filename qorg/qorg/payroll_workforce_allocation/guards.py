import frappe
from frappe import _

def assert_not_payroll_allocated(source_doctype, source_name):
    if source_doctype == "Salary Slip":
        linked = frappe.db.exists("Payroll Allocation Result", {"salary_slip": source_name, "parenttype": "Payroll Allocation Run", "docstatus": 1})
        if linked:
            frappe.throw(_("Salary Slip {0} is already included in a submitted Payroll Allocation Run.").format(source_name))
    if source_doctype == "Payroll Entry":
        linked = frappe.db.exists("Payroll Allocation Run", {"payroll_entry": source_name, "docstatus": 1, "status": ["not in", ["Reversed", "Cancelled"]]})
        if linked:
            frappe.throw(_("Payroll Entry {0} is already allocated through Payroll Allocation Run {1}.").format(source_name, linked))

def validate_other_allocation_document(doc, method=None):
    """Block supported shared-cost documents from consuming Payroll sources twice."""
    pairs = []
    for source_field, name_field in (("source_doctype", "source_name"), ("reference_doctype", "reference_name"), ("document_type", "document_name")):
        if doc.meta.has_field(source_field) and doc.meta.has_field(name_field) and doc.get(source_field) and doc.get(name_field):
            pairs.append((doc.get(source_field), doc.get(name_field)))
    for table_field in [field for field in doc.meta.fields if field.fieldtype == "Table"]:
        for row in doc.get(table_field.fieldname) or []:
            for source_field, name_field in (("source_doctype", "source_name"), ("reference_doctype", "reference_name"), ("document_type", "document_name")):
                if row.meta.has_field(source_field) and row.meta.has_field(name_field) and row.get(source_field) and row.get(name_field):
                    pairs.append((row.get(source_field), row.get(name_field)))
    for source_doctype, source_name in pairs:
        if source_doctype in {"Salary Slip", "Payroll Entry"}:
            assert_not_payroll_allocated(source_doctype, source_name)
