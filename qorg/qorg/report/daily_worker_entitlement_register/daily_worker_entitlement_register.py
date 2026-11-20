from __future__ import annotations
import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
    filters=frappe._dict(filters or {})
    conditions=["a.docstatus < 2"]
    values={}
    for field in ("company","accrual_type","operational_status"):
        if filters.get(field): conditions.append(f"a.{field}=%({field})s");values[field]=filters[field]
    if filters.get("from_date"):conditions.append("a.posting_date >= %(from_date)s");values["from_date"]=filters.from_date
    if filters.get("to_date"):conditions.append("a.posting_date <= %(to_date)s");values["to_date"]=filters.to_date
    if filters.get("project"):conditions.append("(l.project=%(project)s or exists(select 1 from `tabCost Distribution Row` d where d.parenttype='Service and Allowance Accrual Line' and d.parent=l.name and d.project=%(project)s))");values["project"]=filters.project
    if filters.get("funding_agreement"):conditions.append("(l.funding_agreement=%(funding_agreement)s or exists(select 1 from `tabCost Distribution Row` d where d.parenttype='Service and Allowance Accrual Line' and d.parent=l.name and d.funding_agreement=%(funding_agreement)s))");values["funding_agreement"]=filters.funding_agreement
    rows=frappe.db.sql(f"""select a.name accrual,a.posting_date,a.accrual_type,a.operational_status,a.company,l.idx,l.beneficiary_name payee_name,l.external_person,l.supplier,l.employee,l.site,l.service_item,l.project,l.cost_center,l.budget_line,l.funding_agreement,l.gross_amount,l.deduction,l.tax_withheld,l.net_payable,l.eligibility_status,a.journal_entry,a.payment_status from `tabService and Allowance Accrual` a join `tabService and Allowance Accrual Line` l on l.parent=a.name where {' and '.join(conditions)} and l.include=1 order by a.posting_date desc,a.name desc,l.idx""",values,as_dict=True)
    columns=[
      {"fieldname":"accrual","label":_("Accrual"),"fieldtype":"Link","options":"Service and Allowance Accrual","width":170},
      {"fieldname":"payee_name","label":_("Payee / Beneficiary"),"fieldtype":"Data","width":200},
      {"fieldname":"posting_date","label":_("Posting Date"),"fieldtype":"Date","width":105},
      {"fieldname":"accrual_type","label":_("Accrual Type"),"fieldtype":"Link","options":"Service and Allowance Type","width":155},
      {"fieldname":"site","label":_("Site"),"fieldtype":"Data","width":150},
      {"fieldname":"project","label":_("Project"),"fieldtype":"Link","options":"Project","width":150},
      {"fieldname":"budget_line","label":_("Budget Line"),"fieldtype":"Link","options":"Budget Line","width":150},
      {"fieldname":"funding_agreement","label":_("Funding Agreement"),"fieldtype":"Link","options":"Funding Agreement","width":150},
      {"fieldname":"gross_amount","label":_("Gross Amount"),"fieldtype":"Currency","width":120},
      {"fieldname":"deduction","label":_("Deductions"),"fieldtype":"Currency","width":110},
      {"fieldname":"tax_withheld","label":_("Tax Withheld"),"fieldtype":"Currency","width":110},
      {"fieldname":"net_payable","label":_("Net Payable"),"fieldtype":"Currency","width":120},
      {"fieldname":"eligibility_status","label":_("Eligibility"),"fieldtype":"Data","width":110},
      {"fieldname":"operational_status","label":_("Status"),"fieldtype":"Data","width":130},
      {"fieldname":"journal_entry","label":_("Journal Entry"),"fieldtype":"Link","options":"Journal Entry","width":160},
      {"fieldname":"payment_status","label":_("Payment Status"),"fieldtype":"Data","width":120},
    ]
    total=flt(sum(flt(x.net_payable) for x in rows)); posted=flt(sum(flt(x.net_payable) for x in rows if x.operational_status in ("Posted","Partially Paid","Paid")));unposted=total-posted
    summary=[{"label":_("Net Payable"),"value":total,"indicator":"Blue","datatype":"Currency"},{"label":_("Posted"),"value":posted,"indicator":"Green","datatype":"Currency"},{"label":_("Pending Posting"),"value":unposted,"indicator":"Orange","datatype":"Currency"},{"label":_("Payee Lines"),"value":len(rows),"indicator":"Blue","datatype":"Int"}]
    chart={"data":{"labels":[_("Posted"),_("Pending Posting")],"datasets":[{"name":_("Amount"),"values":[posted,unposted]}]},"type":"donut"} if total else None
    return columns,rows,None,chart,summary
