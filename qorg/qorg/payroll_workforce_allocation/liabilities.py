import json,frappe
from frappe import _
from frappe.utils import flt,getdate

def liability_policy(company):
    meta=frappe.get_meta("Company")
    return frappe.db.get_value("Company",company,"custom_payroll_liability_allocation_policy") if meta.has_field("custom_payroll_liability_allocation_policy") else "Do Not Split"
def _effective(rule,on_date):return (not rule.effective_from or getdate(rule.effective_from)<=getdate(on_date)) and (not rule.effective_to or getdate(rule.effective_to)>=getdate(on_date))
def resolve_liability_rules(run):
    mode=liability_policy(run.company);rules=[]
    if mode=="Do Not Split":return rules
    policies={x.policy_reference for x in run.result_rows if x.policy_reference}
    for name in policies:
        policy=frappe.get_doc("Payroll Cost Policy",name)
        for row in policy.liability_rules:
            if not row.enable_dimension_split or not row.liability_account or not _effective(row,run.end_date):continue
            if mode=="Split Statutory Liabilities" and not row.get("is_statutory"):continue
            if mode=="Split Selected Liabilities" and not row.enable_dimension_split:continue
            rules.append(row)
    return sorted(rules,key=lambda x:(x.get("priority") or 10,x.idx))
def should_split_liability(mode,rule):
    if mode=="Do Not Split":return False
    if mode=="Split Statutory Liabilities":return bool(rule.get("is_statutory"))
    if mode=="Split Selected Liabilities":return bool(rule.enable_dimension_split)
    return mode=="Split All Payroll Liabilities"
def resolve_liability_basis(run,rule):
    rows=[x for x in run.result_rows if not rule.source_salary_component or x.salary_component==rule.source_salary_component]
    if rule.allocation_basis=="Taxable Earnings Allocation": rows=[x for x in rows if x.component_category=="Allocable Earning"]
    elif rule.allocation_basis=="Net Pay Allocation": rows=[x for x in rows if x.component_category in ("Allocable Earning","Employee Deduction")]
    total=sum(abs(flt(x.company_currency_amount or x.allocated_amount)) for x in rows)
    return [(x,abs(flt(x.company_currency_amount or x.allocated_amount))/total if total else 0) for x in rows]
def build_liability_dimensions(result,rule):
    dims={}
    if rule.copy_project and result.project:dims["project"]=result.project
    if rule.copy_cost_center and result.cost_center:dims["cost_center"]=result.cost_center
    if rule.copy_funding_dimensions:
        if result.funding_agreement:dims["funding_agreement"]=result.funding_agreement
        if result.budget_line:dims["budget_line"]=result.budget_line
        try:dims.update(json.loads(result.dimension_snapshot or "{}"))
        except Exception:pass
    return dims
def liability_accounts_for_company(company):
    accounts=set()
    for name in frappe.get_all("Payroll Cost Policy",filters={"company":company,"docstatus":1},pluck="name",limit_page_length=0):
        for row in frappe.get_doc("Payroll Cost Policy",name).liability_rules:
            if row.liability_account:accounts.add(row.liability_account)
    return accounts
def payment_liability_rows(doc):return [x for x in (doc.references or []) if x.reference_doctype=="Journal Entry"] if hasattr(doc,"references") else []
def validate_payment_dimensions(doc,method=None):
    if frappe.get_meta("Company").has_field("custom_enforce_liability_dimensions_on_payment") and not frappe.db.get_value("Company",doc.company,"custom_enforce_liability_dimensions_on_payment"):
        return []
    accounts=liability_accounts_for_company(doc.company);issues=[]
    if not accounts:return issues
    gl_accounts={x.account for x in getattr(doc,"accounts",[]) if x.account in accounts}
    if not gl_accounts:
        for field in ("paid_from","paid_to"):
            if doc.get(field) in accounts:gl_accounts.add(doc.get(field))
    if not gl_accounts:return issues
    required=[]
    for name in frappe.get_all("Payroll Cost Policy",filters={"company":doc.company,"docstatus":1},pluck="name",limit_page_length=0):
        required.extend(x for x in frappe.get_doc("Payroll Cost Policy",name).liability_rules if x.liability_account in gl_accounts and x.require_dimensions_on_payment)
    for rule in required:
        for field,enabled in (("project",rule.copy_project),("cost_center",rule.copy_cost_center),("funding_agreement",rule.copy_funding_dimensions),("budget_line",rule.copy_funding_dimensions)):
            if enabled and doc.meta.has_field(field) and not doc.get(field):issues.append(_("{0} is required for payroll liability payment account {1}.").format(field,rule.liability_account))
    if issues:frappe.throw("<br>".join(issues))
    return issues
def reconcile_liability_payment(run):
    rules=resolve_liability_rules(run);accounts={x.liability_account for x in rules};accrued=paid=0;payments=[]
    if run.journal_entry and accounts:
        accrued=flt(frappe.db.sql("select coalesce(sum(credit-debit),0) from `tabGL Entry` where voucher_type='Journal Entry' and voucher_no=%s and account in %s and is_cancelled=0",(run.journal_entry,tuple(accounts)))[0][0])
        payments=frappe.get_all("Payment Entry Reference",filters={"reference_doctype":"Journal Entry","reference_name":run.journal_entry,"docstatus":1},pluck="parent",limit_page_length=0) if frappe.db.exists("DocType","Payment Entry Reference") else []
        if payments:paid=flt(frappe.db.sql("select coalesce(sum(debit-credit),0) from `tabGL Entry` where voucher_type='Payment Entry' and voucher_no in %s and account in %s and is_cancelled=0",(tuple(payments),tuple(accounts)))[0][0])
    outstanding=flt(accrued-paid);status="Matched" if abs(outstanding)<0.01 else ("Partially Matched" if paid else "Pending")
    return {"accrued":accrued,"paid":paid,"outstanding":outstanding,"status":status,"accounts":sorted(accounts),"payment_entries":payments}
def validate_liability_configuration(run):
    mode=liability_policy(run.company)
    if mode=="Do Not Split":return []
    rules=resolve_liability_rules(run);return [] if rules else [_('No effective Payroll Liability Rule is available for the selected liability allocation mode.')]
