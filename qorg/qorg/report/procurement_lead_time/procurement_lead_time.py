import frappe

def execute(filters=None):
    filters=filters or {}
    columns=[{'label': 'Process', 'fieldname': 'name', 'fieldtype': 'Link', 'width': 180, 'options': 'Procurement Process'}, {'label': 'Status', 'fieldname': 'status', 'fieldtype': 'Data', 'width': 170}, {'label': 'Created', 'fieldname': 'creation', 'fieldtype': 'Datetime', 'width': 150}, {'label': 'Modified', 'fieldname': 'modified', 'fieldtype': 'Datetime', 'width': 150}, {'label': 'Deadline', 'fieldname': 'submission_deadline', 'fieldtype': 'Datetime', 'width': 150}]
    fields=[c["fieldname"] for c in columns]
    data=frappe.get_all("Procurement Process",fields=fields,filters={k:v for k,v in filters.items() if v},order_by="modified desc",limit_page_length=500)
    return columns,data
