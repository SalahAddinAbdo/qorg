import frappe
from frappe import _
def execute(filters=None):
 f=frappe._dict(filters or {});values={"company":f.company};where="company=%(company)s and status='Active'"
 rows=frappe.db.sql(f"""select allocation_profile,source_doctype,sum(case when source_doctype in ('Material Request','Supplier Quotation','Purchase Order') then distributed_amount else 0 end) planned_amount,sum(case when source_doctype in ('Purchase Invoice','Expense Claim','Stock Entry','Service Allowance Accrual') then distributed_amount else 0 end) actual_amount from `tabCost Distribution Ledger` where {where} group by allocation_profile,source_doctype order by allocation_profile,source_doctype""",values,as_dict=True)
 for r in rows:r.variance=(r.planned_amount or 0)-(r.actual_amount or 0)
 cols=[{"fieldname":"allocation_profile","label":_("Profile"),"fieldtype":"Link","options":"Cost Distribution Profile","width":190},{"fieldname":"source_doctype","label":_("Source Type"),"width":160},{"fieldname":"planned_amount","label":_("Planned"),"fieldtype":"Currency","width":130},{"fieldname":"actual_amount","label":_("Actual"),"fieldtype":"Currency","width":130},{"fieldname":"variance","label":_("Variance"),"fieldtype":"Currency","width":130}]
 return cols,rows
