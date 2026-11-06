import frappe

def execute(filters=None):
 filters=filters or {}
 columns=[{'label': 'Submission', 'fieldname': 'name', 'fieldtype': 'Link', 'width': 180, 'options': 'Procurement Submission'}, {'label': 'Process', 'fieldname': 'procurement_process', 'fieldtype': 'Link', 'width': 180, 'options': 'Procurement Process'}, {'label': 'Supplier', 'fieldname': 'supplier', 'fieldtype': 'Link', 'width': 160, 'options': 'Supplier'}, {'label': 'Version', 'fieldname': 'submission_version', 'fieldtype': 'Int', 'width': 80}, {'label': 'Supersedes', 'fieldname': 'supersedes_submission', 'fieldtype': 'Link', 'width': 180, 'options': 'Procurement Submission'}, {'label': 'Status', 'fieldname': 'submission_status', 'fieldtype': 'Data', 'width': 120}, {'label': 'Submitted At', 'fieldname': 'submitted_at', 'fieldtype': 'Datetime', 'width': 150}]
 data=frappe.get_all("Procurement Submission",fields=[c["fieldname"] for c in columns],filters={k:v for k,v in filters.items() if v},order_by="modified desc",limit_page_length=500)
 return columns,data
