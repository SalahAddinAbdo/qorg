import json,frappe
from frappe.utils import flt,now_datetime
from .posting import component_account
from .liabilities import reconcile_liability_payment,liability_policy

def _key(account,row):
    dims={}
    try:dims=json.loads(row.dimension_snapshot or "{}")
    except Exception:pass
    return (account,row.project or '',row.cost_center or '',row.funding_agreement or '',row.budget_line or '',json.dumps(dims,sort_keys=True),row.currency or '')
def _gl_key(row):
    meta=frappe.get_meta("GL Entry");dims={}
    if frappe.db.exists("DocType","Accounting Dimension"):
        for dim in frappe.get_all("Accounting Dimension",filters={"disabled":0},fields=["fieldname"],limit_page_length=0):
            if meta.has_field(dim.fieldname) and row.get(dim.fieldname):dims[dim.fieldname]=row.get(dim.fieldname)
    return (row.account,row.get("project") or '',row.get("cost_center") or '',row.get("funding_agreement") or '',row.get("budget_line") or '',json.dumps(dims,sort_keys=True),row.get("account_currency") or '')
def reconcile_run(run):
    expected={};actual={}
    for row in run.result_rows:
        account=component_account(row.salary_component,run.company);key=_key(account,row);expected[key]=expected.get(key,0)+flt(row.company_currency_amount or row.allocated_amount)
    if run.journal_entry:
        fields=["account","debit","credit","project","cost_center","account_currency"]
        meta=frappe.get_meta("GL Entry")
        for f in ("funding_agreement","budget_line"):
            if meta.has_field(f):fields.append(f)
        if frappe.db.exists("DocType","Accounting Dimension"):
            fields.extend(x.fieldname for x in frappe.get_all("Accounting Dimension",filters={"disabled":0},fields=["fieldname"],limit_page_length=0) if x.fieldname not in fields and meta.has_field(x.fieldname))
        for row in frappe.get_all("GL Entry",filters={"voucher_type":"Journal Entry","voucher_no":run.journal_entry,"is_cancelled":0},fields=fields,limit_page_length=0):
            if flt(row.debit)<=0:continue
            key=_gl_key(row);actual[key]=actual.get(key,0)+flt(row.debit-row.credit)
    run.set("reconciliation_details",[])
    total_difference=0
    for key in sorted(set(expected)|set(actual)):
        exp,act=flt(expected.get(key)),flt(actual.get(key));diff=flt(exp-act);total_difference+=diff;account,project,cost_center,agreement,line,dims,currency=key
        run.append("reconciliation_details",{"layer":"GL Entry","reference_type":"Journal Entry","reference_name":run.journal_entry,"account":account,"project":project,"cost_center":cost_center,"funding_agreement":agreement,"budget_line":line,"currency":currency,"expected_amount":exp,"actual_amount":act,"difference":diff,"status":"Matched" if abs(diff)<0.01 else "Difference","exception_code":"" if abs(diff)<0.01 else "GL_DIMENSION_DIFFERENCE","reconciled_on":now_datetime(),"reconciled_by":frappe.session.user,"dimension_key":dims})
    liability=reconcile_liability_payment(run);liability_status=liability["status"] if liability_policy(run.company)!="Do Not Split" else "Not Applicable"
    status="Matched" if abs(total_difference)<0.01 and liability_status in ("Matched","Not Applicable") else ("Partially Matched" if abs(total_difference)<0.01 else "Difference")
    return {"expected_total":sum(expected.values()),"actual_total":sum(actual.values()),"difference":flt(total_difference),"liability":liability,"liability_status":liability_status,"payment_status":liability_status,"status":status}
