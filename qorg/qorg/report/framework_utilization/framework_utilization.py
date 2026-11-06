import frappe
from frappe import _

def execute(filters=None):
    filters=filters or {}
    columns=[{'label': 'Agreement', 'fieldname': 'name', 'fieldtype': 'Link', 'width': 180, 'options': 'Framework Agreement'}, {'label': 'Status', 'fieldname': 'status', 'fieldtype': 'Data', 'width': 120}, {'label': 'Ceiling', 'fieldname': 'total_ceiling', 'fieldtype': 'Currency', 'width': 130}, {'label': 'Consumed', 'fieldname': 'consumed_amount', 'fieldtype': 'Currency', 'width': 130}, {'label': 'Valid From', 'fieldname': 'valid_from', 'fieldtype': 'Date', 'width': 100}, {'label': 'Valid To', 'fieldname': 'valid_to', 'fieldtype': 'Date', 'width': 100}]
    fields=[c["fieldname"] for c in columns]
    data=frappe.get_all("Framework Agreement", fields=fields, filters={k:v for k,v in filters.items() if v}, order_by="modified desc", limit_page_length=500)
    return columns, data
