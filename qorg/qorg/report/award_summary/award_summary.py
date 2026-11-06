import frappe
from frappe import _

def execute(filters=None):
    filters=filters or {}
    columns=[{'label': 'Supplier', 'fieldname': 'supplier', 'fieldtype': 'Link', 'width': 180, 'options': 'Supplier'}, {'label': 'Submission', 'fieldname': 'submission', 'fieldtype': 'Link', 'width': 180, 'options': 'Procurement Submission'}, {'label': 'Technical', 'fieldname': 'technical_score', 'fieldtype': 'Float', 'width': 100}, {'label': 'Financial', 'fieldname': 'financial_score', 'fieldtype': 'Float', 'width': 100}, {'label': 'Total', 'fieldname': 'total_score', 'fieldtype': 'Float', 'width': 100}, {'label': 'Rank', 'fieldname': 'rank', 'fieldtype': 'Int', 'width': 70}, {'label': 'Recommendation', 'fieldname': 'recommendation', 'fieldtype': 'Data', 'width': 150}]
    fields=[c["fieldname"] for c in columns]
    data=frappe.get_all("Bid Summary Row", fields=fields, filters={k:v for k,v in filters.items() if v}, order_by="modified desc", limit_page_length=500)
    return columns, data
