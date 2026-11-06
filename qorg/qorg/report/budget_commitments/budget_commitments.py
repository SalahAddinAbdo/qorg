import frappe

def execute(filters=None):
    filters=filters or {}
    columns=[{'label': 'Ledger', 'fieldname': 'name', 'fieldtype': 'Link', 'width': 180, 'options': 'Commitment Ledger'}, {'label': 'Project', 'fieldname': 'project', 'fieldtype': 'Link', 'width': 150, 'options': 'Project'}, {'label': 'Budget Line', 'fieldname': 'budget_line', 'fieldtype': 'Link', 'width': 160, 'options': 'Budget Line'}, {'label': 'Requested', 'fieldname': 'requested', 'fieldtype': 'Currency', 'width': 110}, {'label': 'Ordered', 'fieldname': 'ordered', 'fieldtype': 'Currency', 'width': 110}, {'label': 'Contracted', 'fieldname': 'contracted', 'fieldtype': 'Currency', 'width': 110}, {'label': 'Invoiced', 'fieldname': 'invoiced', 'fieldtype': 'Currency', 'width': 110}, {'label': 'Paid', 'fieldname': 'paid', 'fieldtype': 'Currency', 'width': 110}]
    fields=[c["fieldname"] for c in columns]
    data=frappe.get_all("Commitment Ledger",fields=fields,filters={k:v for k,v in filters.items() if v},order_by="modified desc",limit_page_length=500)
    return columns,data
