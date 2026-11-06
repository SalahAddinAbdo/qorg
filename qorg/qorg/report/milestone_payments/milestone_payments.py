import frappe

def execute(filters=None):
 filters=filters or {}
 columns=[{'label': 'Contract', 'fieldname': 'parent', 'fieldtype': 'Link', 'width': 180, 'options': 'Procurement Contract'}, {'label': 'Milestone', 'fieldname': 'milestone', 'fieldtype': 'Data', 'width': 220}, {'label': 'Due Date', 'fieldname': 'due_date', 'fieldtype': 'Date', 'width': 100}, {'label': 'Amount', 'fieldname': 'amount', 'fieldtype': 'Currency', 'width': 120}, {'label': 'Percentage', 'fieldname': 'percentage', 'fieldtype': 'Percent', 'width': 90}, {'label': 'Status', 'fieldname': 'status', 'fieldtype': 'Data', 'width': 120}]
 data=frappe.get_all("Contract Milestone",fields=[c["fieldname"] for c in columns],filters={k:v for k,v in filters.items() if v},order_by="modified desc",limit_page_length=500)
 return columns,data
