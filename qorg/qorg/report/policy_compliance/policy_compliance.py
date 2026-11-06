import frappe

def execute(filters=None):
    filters=filters or {}
    columns=[{'label': 'Process', 'fieldname': 'name', 'fieldtype': 'Link', 'width': 180, 'options': 'Procurement Process'}, {'label': 'Policy', 'fieldname': 'policy_rule', 'fieldtype': 'Link', 'width': 170, 'options': 'Procurement Policy Rule'}, {'label': 'Method', 'fieldname': 'procurement_method', 'fieldtype': 'Link', 'width': 170, 'options': 'Procurement Method'}, {'label': 'Status', 'fieldname': 'status', 'fieldtype': 'Data', 'width': 160}, {'label': 'Estimated Value', 'fieldname': 'estimated_value', 'fieldtype': 'Currency', 'width': 130}]
    fields=[c["fieldname"] for c in columns]
    data=frappe.get_all("Procurement Process",fields=fields,filters={k:v for k,v in filters.items() if v},order_by="modified desc",limit_page_length=500)
    return columns,data
