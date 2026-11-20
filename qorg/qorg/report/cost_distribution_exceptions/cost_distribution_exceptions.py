import frappe
from frappe import _
def execute(filters=None):
 f=frappe._dict(filters or {});values={"company":f.company};rows=frappe.db.sql("""select source_doctype,source_document,source_row,original_amount,distributed_amount,remaining_amount,status,allocation_profile from `tabCost Distribution Ledger` where company=%(company)s and (abs(remaining_amount)>0.01 or status in ('Cancelled','Reversed')) order by modified desc""",values,as_dict=True)
 cols=[{"fieldname":"source_doctype","label":_("Source Type"),"width":160},{"fieldname":"source_document","label":_("Source Document"),"width":180},{"fieldname":"source_row","label":_("Source Row"),"width":160},{"fieldname":"allocation_profile","label":_("Profile"),"fieldtype":"Link","options":"Cost Distribution Profile","width":180},{"fieldname":"original_amount","label":_("Original"),"fieldtype":"Currency","width":120},{"fieldname":"distributed_amount","label":_("Distributed"),"fieldtype":"Currency","width":120},{"fieldname":"remaining_amount","label":_("Difference"),"fieldtype":"Currency","width":120},{"fieldname":"status","label":_("Status"),"width":110}]
 return cols,rows
