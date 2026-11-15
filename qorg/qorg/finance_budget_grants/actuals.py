from __future__ import annotations
import frappe
from frappe.utils import flt

def get_posted_actual(project=None,budget_line=None,company=None,from_date=None,to_date=None):
    filters=["is_cancelled = 0","account is not null"]
    values={}
    for key,value in (("project",project),("budget_line",budget_line),("company",company)):
        if value: filters.append(f"{key} = %({key})s"); values[key]=value
    if from_date: filters.append("posting_date >= %(from_date)s");values["from_date"]=from_date
    if to_date: filters.append("posting_date <= %(to_date)s");values["to_date"]=to_date
    amount=frappe.db.sql(f"select coalesce(sum(debit-credit),0) from `tabGL Entry` where {' and '.join(filters)}",values)[0][0]
    return flt(amount)
