import frappe
from frappe.utils import flt
from .permissions import assert_report_access

def company_currency(company):return frappe.db.get_value("Company",company,"default_currency") if company else None
def safe_filters(filters=None):return frappe._dict(filters or {}),assert_report_access()
def summary(value,label,datatype="Currency",indicator=None):return {"value":value,"label":label,"datatype":datatype,"indicator":indicator}
def col(field,label,fieldtype="Data",options=None,width=150,freeze=False):
    out={"fieldname":field,"label":label,"fieldtype":fieldtype,"width":width}
    if options:out["options"]=options
    if freeze:out["freeze"]=1
    return out
def run_names(filters):
    f=frappe._dict(filters or {});where={"docstatus":1}
    for k in ("company","status","reconciliation_status"):
        if f.get(k):where[k]=f.get(k)
    if f.get("from_date"):where["posting_date"]=[">=",f.from_date]
    if f.get("to_date"):
        if "posting_date" in where and isinstance(where["posting_date"],list):where["posting_date"]=["between",[f.from_date,f.to_date]]
        else:where["posting_date"]=["<=",f.to_date]
    return frappe.get_all("Payroll Allocation Run",filters=where,pluck="name",limit_page_length=0)
def allocation_rows(filters=None):
    f,access=safe_filters(filters);runs=set(run_names(f));where={"parenttype":"Payroll Allocation Run","docstatus":1}
    for k in ("project","funding_agreement","budget_line"):
        if f.get(k):where[k]=f.get(k)
    rows=frappe.get_all("Payroll Allocation Result",filters=where,fields=["parent as allocation_run","employee","salary_component","project","cost_center","funding_agreement","budget_line","funding_type","work_share","allocated_amount","company_currency_amount","currency"],limit_page_length=0)
    rows=[x for x in rows if x.allocation_run in runs]
    if access["aggregate_only"]:
        grouped={}
        for x in rows:
            k=(x.project,x.funding_agreement,x.budget_line,x.currency);g=grouped.setdefault(k,frappe._dict(project=x.project,funding_agreement=x.funding_agreement,budget_line=x.budget_line,currency=x.currency,company_currency_amount=0,allocated_amount=0,work_share=0));g.company_currency_amount+=flt(x.company_currency_amount);g.allocated_amount+=flt(x.allocated_amount);g.work_share+=flt(x.work_share)
        return list(grouped.values())
    return rows
def reconciliation_rows(filters=None):
    f,access=safe_filters(filters);where={"name":["in",run_names(f)]}
    fields=["name","company","payroll_entry","posting_date","company_currency","total_employment_cost","total_allocated_cost","allocation_difference","journal_entry","reversal_journal_entry","reconciliation_status","liability_reconciliation_status","payment_reconciliation_status","commitment_status","status"]
    out=[]
    for run in frappe.get_all("Payroll Allocation Run",filters=where,fields=fields,order_by="posting_date desc,name desc",limit_page_length=0):
        gl=frappe.db.get_value("Journal Entry",run.journal_entry,["total_debit","total_credit"],as_dict=True) if run.journal_entry else {};debit=flt((gl or {}).get("total_debit"));credit=flt((gl or {}).get("total_credit"));run.update(journal_debit=debit,journal_credit=credit,journal_difference=flt(debit-credit),result_vs_gl_difference=flt(run.total_allocated_cost-debit));out.append(run)
    return out
def liability_rows(filters=None):
    f,access=safe_filters(filters);from qorg.qorg.payroll_workforce_allocation.liabilities import reconcile_liability_payment
    rows=[]
    for name in run_names(f):
        run=frappe.get_doc("Payroll Allocation Run",name);result=reconcile_liability_payment(run)
        for account in result["accounts"]:rows.append(frappe._dict(allocation_run=run.name,company=run.company,payroll_entry=run.payroll_entry,status=run.status,account=account,accrued=result["accrued"],paid=result["paid"],outstanding=result["outstanding"],liability_reconciliation_status=run.liability_reconciliation_status,payment_reconciliation_status=run.payment_reconciliation_status))
    return rows
