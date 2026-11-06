import frappe
from frappe import _

def execute(filters=None):
    filters=filters or {}
    columns=[{'label': 'Parent', 'fieldname': 'parent', 'fieldtype': 'Dynamic Link', 'width': 180}, {'label': 'Type', 'fieldname': 'guarantee_type', 'fieldtype': 'Data', 'width': 180}, {'label': 'Issuer', 'fieldname': 'issuer', 'fieldtype': 'Data', 'width': 160}, {'label': 'Amount', 'fieldname': 'amount', 'fieldtype': 'Currency', 'width': 120}, {'label': 'Valid To', 'fieldname': 'valid_to', 'fieldtype': 'Date', 'width': 100}, {'label': 'Status', 'fieldname': 'status', 'fieldtype': 'Data', 'width': 100}]
    fields=[c["fieldname"] for c in columns]
    data=frappe.get_all("Guarantee Row", fields=fields, filters={k:v for k,v in filters.items() if v}, order_by="modified desc", limit_page_length=500)
    return columns, data
