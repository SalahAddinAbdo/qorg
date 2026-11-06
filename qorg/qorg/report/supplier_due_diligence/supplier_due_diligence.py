import frappe
from frappe import _

def execute(filters=None):
    filters=filters or {}
    columns=[{'label': 'Registration', 'fieldname': 'name', 'fieldtype': 'Link', 'width': 180, 'options': 'Supplier Registration'}, {'label': 'Legal Name', 'fieldname': 'legal_name', 'fieldtype': 'Data', 'width': 220}, {'label': 'Status', 'fieldname': 'registration_status', 'fieldtype': 'Data', 'width': 150}, {'label': 'Risk', 'fieldname': 'risk_rating', 'fieldtype': 'Data', 'width': 90}, {'label': 'Review Expiry', 'fieldname': 'review_expiry_date', 'fieldtype': 'Date', 'width': 110}, {'label': 'Supplier', 'fieldname': 'supplier', 'fieldtype': 'Link', 'width': 160, 'options': 'Supplier'}]
    fields=[c["fieldname"] for c in columns]
    data=frappe.get_all("Supplier Registration", fields=fields, filters={k:v for k,v in filters.items() if v}, order_by="modified desc", limit_page_length=500)
    return columns, data
