import hashlib
import json
import frappe
from frappe.utils import flt, now_datetime

def _sync_key(company,fiscal_year,project): return f"QORG|{company}|{fiscal_year}|Project|{project}"
def _digest(rows): return hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()

def collect_project_budget(project,fiscal_year):
    company=frappe.db.get_value("Project",project,"company")
    if not company: frappe.throw("Project must have a Company")
    rows=frappe.db.sql("""select bl.name budget_line,bl.erpnext_account account,sum(pa.allocated_amount) amount from `tabBudget Line` bl inner join `tabBudget Period Allocation` pa on pa.parent=bl.name inner join `tabBudget Period` bp on bp.name=pa.budget_period where bl.project=%s and bp.company=%s and bp.fiscal_year=%s and bl.is_group=0 group by bl.name,bl.erpnext_account order by bl.name""",(project,company,fiscal_year),as_dict=True)
    missing=[r.budget_line for r in rows if not r.account and flt(r.amount)]
    if missing: frappe.throw("ERPNext Account is required for Budget Lines: "+", ".join(missing))
    totals={}
    for r in rows:
        if r.account: totals[r.account]=totals.get(r.account,0)+flt(r.amount)
    normalized=[{"account":a,"budget_amount":totals[a]} for a in sorted(totals)]
    return company,normalized,rows

def sync_project_budget(project,fiscal_year,dry_run=False):
    company,accounts,source_rows=collect_project_budget(project,fiscal_year)
    if not accounts: return {"status":"Skipped","message":"No period allocations found","project":project,"fiscal_year":fiscal_year}
    key=_sync_key(company,fiscal_year,project);signature=_digest(accounts)
    existing=frappe.db.get_value("Budget",{"qorg_sync_key":key},"name")
    if existing:
        doc=frappe.get_doc("Budget",existing)
        if not doc.qorg_managed_budget: frappe.throw("Refusing to overwrite an ERPNext Budget not managed by QOrg")
    else:
        # Never adopt a manually-created Budget merely because dimensions match.
        doc=frappe.new_doc("Budget");doc.company=company;doc.fiscal_year=fiscal_year;doc.budget_against="Project";doc.project=project;doc.qorg_managed_budget=1;doc.qorg_sync_key=key
    result={"status":"Preview" if dry_run else "Synced","budget":doc.name or None,"company":company,"project":project,"fiscal_year":fiscal_year,"accounts":accounts,"sync_hash":signature}
    if dry_run:return result
    doc.set("accounts",[])
    for row in accounts: doc.append("accounts",row)
    doc.qorg_last_synced_on=now_datetime()
    if doc.is_new():doc.insert(ignore_permissions=True)
    else:doc.save(ignore_permissions=True)
    for r in source_rows:
        frappe.db.set_value("Budget Line",r.budget_line,{"erpnext_budget":doc.name,"erpnext_sync_status":"Synced","erpnext_sync_hash":signature,"erpnext_synced_on":doc.qorg_last_synced_on,"erpnext_sync_message":f"Synced to {doc.name} for {fiscal_year}"},update_modified=False)
    result["budget"]=doc.name
    return result

@frappe.whitelist()
def preview_project_budget(project,fiscal_year):
    frappe.has_permission("Budget","read",throw=True);return sync_project_budget(project,fiscal_year,True)

@frappe.whitelist()
def sync(project,fiscal_year):
    frappe.has_permission("Budget","write",throw=True);return sync_project_budget(project,fiscal_year,False)

def mark_unsynced(doc,method=None):
    if doc.is_group:return
    if doc.get("erpnext_sync_status")=="Synced":
        frappe.db.set_value("Budget Line",doc.name,{"erpnext_sync_status":"Not Synced","erpnext_sync_message":"Budget Line changed after last sync"},update_modified=False)
