import frappe
from frappe import _
def execute(filters=None):
 filters=frappe._dict(filters or {});conditions=["company=%(company)s"];values={"company":filters.company}
 if filters.get("source_doctype"):conditions.append("source_doctype=%(source_doctype)s");values["source_doctype"]=filters.source_doctype
 if filters.get("status"):conditions.append("status=%(status)s");values["status"]=filters.status
 rows=frappe.db.sql(f"select name,source_doctype,source_document,source_row,allocation_profile,original_amount,distributed_amount,remaining_amount,status,allocation_mode,journal_entry from `tabCost Distribution Ledger` where {' and '.join(conditions)} order by modified desc",values,as_dict=True)
 cols=[{"fieldname":"name","label":_("Ledger"),"fieldtype":"Link","options":"Cost Distribution Ledger","width":170},{"fieldname":"source_doctype","label":_("Source Type"),"width":150},{"fieldname":"source_document","label":_("Source Document"),"width":180},{"fieldname":"source_row","label":_("Source Row"),"width":150},{"fieldname":"allocation_profile","label":_("Profile"),"fieldtype":"Link","options":"Cost Distribution Profile","width":160},{"fieldname":"original_amount","label":_("Original"),"fieldtype":"Currency","width":110},{"fieldname":"distributed_amount","label":_("Distributed"),"fieldtype":"Currency","width":110},{"fieldname":"remaining_amount","label":_("Remaining"),"fieldtype":"Currency","width":110},{"fieldname":"status","label":_("Status"),"width":100},{"fieldname":"journal_entry","label":_("Journal Entry"),"fieldtype":"Link","options":"Journal Entry","width":160}]
 return cols,rows
