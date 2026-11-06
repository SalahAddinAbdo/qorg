import frappe

def execute(filters=None):
    filters=filters or {}
    columns=[{'label': 'Complaint', 'fieldname': 'name', 'fieldtype': 'Link', 'width': 180, 'options': 'Procurement Complaint'}, {'label': 'Process', 'fieldname': 'procurement_process', 'fieldtype': 'Link', 'width': 180, 'options': 'Procurement Process'}, {'label': 'Supplier', 'fieldname': 'supplier', 'fieldtype': 'Link', 'width': 160, 'options': 'Supplier'}, {'label': 'Type', 'fieldname': 'complaint_type', 'fieldtype': 'Data', 'width': 130}, {'label': 'Status', 'fieldname': 'status', 'fieldtype': 'Data', 'width': 130}, {'label': 'Received', 'fieldname': 'received_on', 'fieldtype': 'Datetime', 'width': 150}, {'label': 'Closed', 'fieldname': 'closed_on', 'fieldtype': 'Datetime', 'width': 150}]
    fields=[c["fieldname"] for c in columns]
    data=frappe.get_all("Procurement Complaint",fields=fields,filters={k:v for k,v in filters.items() if v},order_by="modified desc",limit_page_length=500)
    return columns,data
