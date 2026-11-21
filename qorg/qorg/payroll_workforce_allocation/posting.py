import json,frappe
from frappe import _
from frappe.utils import flt
from .dimensions import apply_dimensions
from .liabilities import resolve_liability_rules,resolve_liability_basis,build_liability_dimensions

def _company_value(company,field):return frappe.db.get_value("Company",company,field) if frappe.get_meta("Company").has_field(field) else None
def component_account(component,company):return frappe.db.get_value("Salary Component Account",{"parent":component,"company":company},"account") if frappe.db.exists("DocType","Salary Component Account") else None
def payroll_accrual_journal(run):
    pe=frappe.get_doc("Payroll Entry",run.payroll_entry)
    for field in ("journal_entry","accrual_jv","salary_slip_journal_entry"):
        if pe.meta.has_field(field) and pe.get(field):return pe.get(field)
    if frappe.get_meta("Journal Entry").has_field("payroll_entry"):
        rows=frappe.get_all("Journal Entry",filters={"payroll_entry":run.payroll_entry,"docstatus":1},pluck="name",order_by="posting_date desc,modified desc",limit=2)
        if len(rows)==1:return rows[0]
def _dimensions(row):
    out={"project":row.project,"cost_center":row.cost_center,"funding_agreement":row.funding_agreement,"budget_line":row.budget_line}
    try:out.update(json.loads(row.dimension_snapshot or "{}"))
    except Exception:pass
    return {k:v for k,v in out.items() if v}
def _append(je,account,debit,credit,dimensions,ref=None):
    row=je.append("accounts",{"account":account,"debit_in_account_currency":flt(debit),"credit_in_account_currency":flt(credit)})
    apply_dimensions(row,dimensions or {})
    if ref and row.meta.has_field("reference_type"):row.reference_type="Payroll Entry";row.reference_name=ref
    return row
def _assert_balanced(je):
    d=sum(flt(x.debit_in_account_currency) for x in je.accounts);c=sum(flt(x.credit_in_account_currency) for x in je.accounts);difference=flt(d-c,2)
    if abs(difference)>0 and abs(difference)<=0.05:
        account=_company_value(je.company,"custom_payroll_allocation_rounding_account")
        if account:_append(je,account,0 if difference>0 else abs(difference),difference if difference>0 else 0,{"cost_center":_company_value(je.company,"cost_center")});d=sum(flt(x.debit_in_account_currency) for x in je.accounts);c=sum(flt(x.credit_in_account_currency) for x in je.accounts)
    if abs(d-c)>0.005:frappe.throw(_("Payroll reclassification Journal Entry is not balanced. Debit {0}, Credit {1}. Configure a Payroll Allocation Rounding Account for small currency differences.").format(d,c))
def _accrual_gl(accrual):
    # Reads submitted rows from tabGL Entry through the Frappe ORM.
    fields=["account","debit","credit","project","cost_center","account_currency"]
    meta=frappe.get_meta("GL Entry")
    for f in ("funding_agreement","budget_line"):
        if meta.has_field(f):fields.append(f)
    return frappe.get_all("GL Entry",filters={"voucher_type":"Journal Entry","voucher_no":accrual,"is_cancelled":0},fields=fields,limit_page_length=0)
def _source_rows(gl,account,debit=True):return [x for x in gl if x.account==account and (flt(x.debit)>0 if debit else flt(x.credit)>0)]
def _source_dims(row):return {k:row.get(k) for k in ("project","cost_center","funding_agreement","budget_line") if row.get(k)}
def _assert_clearing_funded(run,clearing_account,required_amount):
    accrual=payroll_accrual_journal(run)
    if not accrual:frappe.throw(_("No submitted Payroll accrual Journal Entry is linked to Payroll Entry {0}.").format(run.payroll_entry))
    funded=sum(abs(flt(x.debit-x.credit)) for x in _accrual_gl(accrual) if x.account==clearing_account)
    if funded+0.005<flt(required_amount):frappe.throw(_("Payroll accrual does not fund the clearing account sufficiently."))
    return accrual
def _posting_mode(run,gl,clearing,total):
    funded=sum(abs(flt(x.debit-x.credit)) for x in gl if x.account==clearing)
    return "Clearing Funded" if clearing and funded+0.005>=total else "Source Account Reclassification"
def _expense_rows(je,run,gl,mode,clearing):
    by_account={};total=0
    for result in run.result_rows:
        amount=flt(result.company_currency_amount or result.allocated_amount);account=component_account(result.salary_component,run.company)
        if not account:frappe.throw(_("No component account is configured for Salary Component {0}.").format(result.salary_component))
        _append(je,account,amount,0,_dimensions(result),run.payroll_entry);by_account[account]=by_account.get(account,0)+amount;total+=amount
    if mode=="Clearing Funded":_append(je,clearing,0,total,{"cost_center":_company_value(run.company,"cost_center")},run.payroll_entry)
    else:
        for account,amount in by_account.items():
            source=_source_rows(gl,account,True)
            if not source or sum(flt(x.debit-x.credit) for x in source)+0.005<amount:frappe.throw(_("Payroll accrual does not contain enough source expense for account {0}.").format(account))
            remaining=amount
            for row in source:
                take=min(remaining,flt(row.debit-row.credit));_append(je,account,0,take,_source_dims(row),run.payroll_entry);remaining-=take
                if remaining<=0.005:break
def _liability_rows(je,run,gl):
    for rule in resolve_liability_rules(run):
        account=rule.liability_account;source=_source_rows(gl,account,False);total=sum(flt(x.credit-x.debit) for x in source)
        if total<=0:continue
        basis=resolve_liability_basis(run,rule)
        if not basis:frappe.throw(_("No allocation basis was resolved for liability account {0}.").format(account))
        # Remove the undimensioned/original liability and recreate it by approved dimensions.
        for row in source:_append(je,account,flt(row.credit-row.debit),0,_source_dims(row),run.payroll_entry)
        assigned=0
        for idx,(result,share) in enumerate(basis):
            amount=total-assigned if idx==len(basis)-1 else flt(total*share,2);assigned+=amount
            _append(je,account,0,amount,build_liability_dimensions(result,rule),run.payroll_entry)
def create_reclassification_entry(run):
    if run.journal_entry and frappe.db.exists("Journal Entry",run.journal_entry):return run.journal_entry
    existing=frappe.db.exists("Journal Entry",{"custom_payroll_allocation_run":run.name,"docstatus":["<",2]}) if frappe.get_meta("Journal Entry").has_field("custom_payroll_allocation_run") else None
    if existing:return existing
    accrual=payroll_accrual_journal(run)
    if not accrual:frappe.throw(_("No submitted Payroll accrual Journal Entry is linked to Payroll Entry {0}.").format(run.payroll_entry))
    gl=_accrual_gl(accrual);clearing=_company_value(run.company,"custom_payroll_allocation_clearing_account");total=sum(flt(x.company_currency_amount or x.allocated_amount) for x in run.result_rows);mode=_posting_mode(run,gl,clearing,total)
    je=frappe.new_doc("Journal Entry");je.company=run.company;je.posting_date=run.posting_date or run.end_date;je.voucher_type="Journal Entry";je.user_remark=_("Payroll workforce-cost reclassification for {0} ({1})").format(run.name,mode)
    if je.meta.has_field("custom_payroll_allocation_run"):je.custom_payroll_allocation_run=run.name
    if je.meta.has_field("payroll_entry"):je.payroll_entry=run.payroll_entry
    _expense_rows(je,run,gl,mode,clearing);_liability_rows(je,run,gl);_assert_balanced(je);je.insert(ignore_permissions=True);je.submit();return je.name
def create_reversal_entry(run):
    if run.reversal_journal_entry and frappe.db.exists("Journal Entry",run.reversal_journal_entry):return run.reversal_journal_entry
    if not run.journal_entry:frappe.throw(_("No posted Journal Entry exists to reverse."))
    original=frappe.get_doc("Journal Entry",run.journal_entry)
    if original.docstatus!=1:frappe.throw(_("Only a submitted Journal Entry can be reversed."))
    reversal=frappe.new_doc("Journal Entry");reversal.company=original.company;reversal.posting_date=frappe.utils.today();reversal.voucher_type="Journal Entry";reversal.user_remark=_("Reversal of {0} for Payroll Allocation Run {1}").format(original.name,run.name)
    if reversal.meta.has_field("custom_payroll_allocation_run"):reversal.custom_payroll_allocation_run=run.name
    for source in original.accounts:
        values=source.as_dict(no_nulls=True)
        for key in ("name","parent","parentfield","parenttype","idx"):values.pop(key,None)
        values["debit_in_account_currency"],values["credit_in_account_currency"]=flt(source.credit_in_account_currency),flt(source.debit_in_account_currency);reversal.append("accounts",values)
    _assert_balanced(reversal);reversal.insert(ignore_permissions=True);reversal.submit();return reversal.name
