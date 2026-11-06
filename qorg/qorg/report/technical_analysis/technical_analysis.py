import frappe
from frappe import _

def execute(filters=None):
    filters=filters or {}
    columns=[{'label': 'Evaluation', 'fieldname': 'name', 'fieldtype': 'Link', 'width': 180, 'options': 'Technical Evaluation'}, {'label': 'Process', 'fieldname': 'procurement_process', 'fieldtype': 'Link', 'width': 180, 'options': 'Procurement Process'}, {'label': 'Supplier', 'fieldname': 'supplier', 'fieldtype': 'Link', 'width': 180, 'options': 'Supplier'}, {'label': 'Score', 'fieldname': 'raw_technical_score', 'fieldtype': 'Float', 'width': 110}, {'label': 'Threshold', 'fieldname': 'technical_threshold', 'fieldtype': 'Percent', 'width': 110}, {'label': 'Result', 'fieldname': 'result', 'fieldtype': 'Data', 'width': 120}]
    fields=[c["fieldname"] for c in columns]
    data=frappe.get_all("Technical Evaluation", fields=fields, filters={k:v for k,v in filters.items() if v}, order_by="modified desc", limit_page_length=500)
    return columns, data
