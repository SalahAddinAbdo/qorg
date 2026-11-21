import json,frappe
from frappe import _
from frappe.utils import flt
from .eligibility import available_budget

def lock_payroll_entry(name):frappe.db.sql("select name from `tabPayroll Entry` where name=%s for update",name)
def _groups(run):
    out={}
    for row in run.result_rows:
        if row.budget_line:out[row.budget_line]=out.get(row.budget_line,0)+flt(row.company_currency_amount or row.allocated_amount)
    return out
def _mapping():
    candidates=(
      ("Commitment Entry",{"reference_type":("reference_doctype","reference_type"),"reference_name":("reference_name","reference_document"),"budget_line":("budget_line",),"amount":("reserved_amount","amount","commitment_amount"),"status":("status",),"key":("idempotency_key","snapshot_hash")} ),
      ("Commitment Ledger",{"reference_type":("reference_doctype","reference_type"),"reference_name":("reference_name","reference_document"),"budget_line":("budget_line",),"amount":("reserved_amount","amount","commitment_amount"),"status":("status",),"key":("idempotency_key","snapshot_hash")} ),
    )
    for dt,spec in candidates:
        if not frappe.db.exists("DocType",dt):continue
        meta=frappe.get_meta(dt);resolved={k:next((x for x in names if meta.has_field(x)),None) for k,names in spec.items()}
        if all(resolved[k] for k in ("reference_type","reference_name","budget_line","amount","status","key")):return dt,resolved
    frappe.throw(_("No compatible QOrg Commitment Entry/Ledger mapping is installed. Run the payroll capability audit and complete the finance module first."))
def _upsert(run,line,amount,status):
    dt,m=_mapping();filters={m["reference_type"]:"Payroll Allocation Run",m["reference_name"]:run.name,m["budget_line"]:line};name=frappe.db.exists(dt,filters)
    doc=frappe.get_doc(dt,name) if name else frappe.new_doc(dt)
    for f,v in ((m["reference_type"],"Payroll Allocation Run"),(m["reference_name"],run.name),(m["budget_line"],line),(m["amount"],amount),(m["status"],status),(m["key"],f"{run.name}:{line}:{run.audit_snapshot_hash or run.source_fingerprint}")):doc.set(f,v)
    for f,v in (("company",run.company),("project",next((x.project for x in run.result_rows if x.budget_line==line),None)),("funding_agreement",next((x.funding_agreement for x in run.result_rows if x.budget_line==line),None))):
        if doc.meta.has_field(f):doc.set(f,v)
    if doc.is_new():doc.insert(ignore_permissions=True)
    else:doc.save(ignore_permissions=True)
    if doc.meta.is_submittable and doc.docstatus==0 and status in ("Reserved","Posted"):doc.submit()
    return doc.name
def reserve_run(run):
    refs=[]
    for line,amount in sorted(_groups(run).items()):
        frappe.db.sql("select name from `tabBudget Line` where name=%s for update",line);balance=available_budget(line,run.name)
        if balance["available"]+0.005<amount:frappe.throw(_("Budget Line {0} has {1} available but {2} is required.").format(line,balance["available"],amount))
        refs.append(_upsert(run,line,amount,"Reserved"))
    run.commitment_status="Reserved";run.commitment_references=json.dumps(refs);return refs
def mark_posted(run):
    for line,amount in sorted(_groups(run).items()):_upsert(run,line,amount,"Posted")
    run.db_set("commitment_status","Posted",update_modified=False)
def release_run(run,reversed=False):
    status="Reversed" if reversed else "Released"
    for line in sorted(_groups(run)):_upsert(run,line,0,status)
    run.db_set("commitment_status",status,update_modified=False)
