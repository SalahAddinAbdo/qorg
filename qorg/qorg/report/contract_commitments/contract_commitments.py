import frappe
from frappe import _

def execute(filters=None):
    filters=filters or {}
    columns=[{'label': 'Contract', 'fieldname': 'name', 'fieldtype': 'Link', 'width': 180, 'options': 'Procurement Contract'}, {'label': 'Supplier', 'fieldname': 'supplier', 'fieldtype': 'Link', 'width': 180, 'options': 'Supplier'}, {'label': 'Status', 'fieldname': 'status', 'fieldtype': 'Data', 'width': 120}, {'label': 'Value', 'fieldname': 'contract_value', 'fieldtype': 'Currency', 'width': 130}, {'label': 'Start', 'fieldname': 'start_date', 'fieldtype': 'Date', 'width': 100}, {'label': 'End', 'fieldname': 'end_date', 'fieldtype': 'Date', 'width': 100}, {'label': 'Manager', 'fieldname': 'contract_manager', 'fieldtype': 'Link', 'width': 160, 'options': 'User'}]
    fields=[c["fieldname"] for c in columns]
    data=frappe.get_all("Procurement Contract", fields=fields, filters={k:v for k,v in filters.items() if v}, order_by="modified desc", limit_page_length=500)
    return columns, data
