import frappe
from frappe import _

def execute(filters=None):
    filters=filters or {}
    columns=[{'label': 'Submission', 'fieldname': 'name', 'fieldtype': 'Link', 'width': 180, 'options': 'Procurement Submission'}, {'label': 'Process', 'fieldname': 'procurement_process', 'fieldtype': 'Link', 'width': 180, 'options': 'Procurement Process'}, {'label': 'Supplier', 'fieldname': 'supplier', 'fieldtype': 'Link', 'width': 180, 'options': 'Supplier'}, {'label': 'Status', 'fieldname': 'submission_status', 'fieldtype': 'Data', 'width': 140}, {'label': 'Submitted At', 'fieldname': 'submitted_at', 'fieldtype': 'Datetime', 'width': 165}]
    fields=[c["fieldname"] for c in columns]
    data=frappe.get_all("Procurement Submission", fields=fields, filters={k:v for k,v in filters.items() if v}, order_by="modified desc", limit_page_length=500)
    return columns, data
