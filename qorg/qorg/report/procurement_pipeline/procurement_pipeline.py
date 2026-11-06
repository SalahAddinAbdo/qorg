import frappe
from frappe import _

def execute(filters=None):
    filters=filters or {}
    columns=[{'label': 'Process', 'fieldname': 'name', 'fieldtype': 'Link', 'width': 180, 'options': 'Procurement Process'}, {'label': 'Title', 'fieldname': 'title', 'fieldtype': 'Data', 'width': 220}, {'label': 'Company', 'fieldname': 'company', 'fieldtype': 'Link', 'width': 160, 'options': 'Company'}, {'label': 'Method', 'fieldname': 'procurement_method', 'fieldtype': 'Link', 'width': 170, 'options': 'Procurement Method'}, {'label': 'Status', 'fieldname': 'status', 'fieldtype': 'Data', 'width': 180}, {'label': 'Estimated Value', 'fieldname': 'estimated_value', 'fieldtype': 'Currency', 'width': 140}, {'label': 'Submission Deadline', 'fieldname': 'submission_deadline', 'fieldtype': 'Datetime', 'width': 165}]
    fields=[c["fieldname"] for c in columns]
    data=frappe.get_all("Procurement Process", fields=fields, filters={k:v for k,v in filters.items() if v}, order_by="modified desc", limit_page_length=500)
    return columns, data
