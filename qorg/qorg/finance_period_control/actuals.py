import frappe
from frappe.utils import flt
ASSET_TYPES=("Fixed Asset","Capital Work in Progress","Stock","Stock Received But Not Billed")
def account_clause(basis):
    asset="a.root_type='Asset' and a.account_type in ('Fixed Asset','Capital Work in Progress','Stock','Stock Received But Not Billed')"
    expense="a.root_type='Expense'"
    if basis=="Asset Acquisition":return asset
    if basis=="Expense and Asset Acquisition":return f"(({expense} and coalesce(a.account_type,'')!='Depreciation') or ({asset}))"
    return expense
def actual_for_line(company,budget_line,from_date,to_date,basis=None):
    basis=basis or frappe.db.get_value("Budget Line",budget_line,"recognition_basis") or "Expense Only";clause=account_clause(basis)
    return flt(frappe.db.sql(f"select coalesce(sum(gl.debit-gl.credit),0) from `tabGL Entry` gl inner join `tabAccount` a on a.name=gl.account where gl.is_cancelled=0 and gl.docstatus=1 and gl.company=%s and gl.budget_line=%s and gl.posting_date between %s and %s and ({clause})",(company,budget_line,from_date,to_date))[0][0])
