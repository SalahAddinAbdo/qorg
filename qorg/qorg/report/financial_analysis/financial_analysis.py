import frappe
from frappe import _

def execute(filters=None):
    filters=filters or {}
    columns=[{'label': 'Evaluation', 'fieldname': 'name', 'fieldtype': 'Link', 'width': 180, 'options': 'Financial Evaluation'}, {'label': 'Process', 'fieldname': 'procurement_process', 'fieldtype': 'Link', 'width': 180, 'options': 'Procurement Process'}, {'label': 'Supplier', 'fieldname': 'supplier', 'fieldtype': 'Link', 'width': 180, 'options': 'Supplier'}, {'label': 'Original Price', 'fieldname': 'original_price', 'fieldtype': 'Currency', 'width': 130}, {'label': 'Evaluated Price', 'fieldname': 'evaluated_price', 'fieldtype': 'Currency', 'width': 130}, {'label': 'Financial Score', 'fieldname': 'financial_score', 'fieldtype': 'Float', 'width': 120}]
    fields=[c["fieldname"] for c in columns]
    data=frappe.get_all("Financial Evaluation", fields=fields, filters={k:v for k,v in filters.items() if v}, order_by="modified desc", limit_page_length=500)
    return columns, data
