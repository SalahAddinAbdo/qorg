import frappe

REQUIRED_DOCTYPES=("Budget Period","Budget Period Allocation","Budget Period Resolution Rule","Budget Line","Commitment Ledger","Commitment Entry")
REQUIRED_BUDGET_FIELDS=("qorg_managed_budget","qorg_sync_key","qorg_last_synced_on")
REQUIRED_ENTRY_FIELDS=("event_key","budget_line","base_amount","commitment_period","matching_status","cost_distribution_row","origin_period")

@frappe.whitelist()
def readiness_check():
    frappe.only_for(("System Manager","Accounts Manager"))
    checks=[]
    for doctype in REQUIRED_DOCTYPES:checks.append({"check":f"DocType: {doctype}","ok":bool(frappe.db.exists("DocType",doctype))})
    budget_meta=frappe.get_meta("Budget")
    for field in REQUIRED_BUDGET_FIELDS:checks.append({"check":f"Budget field: {field}","ok":bool(budget_meta.has_field(field))})
    entry_meta=frappe.get_meta("Commitment Entry")
    for field in REQUIRED_ENTRY_FIELDS:checks.append({"check":f"Commitment Entry field: {field}","ok":bool(entry_meta.has_field(field))})
    duplicate_periods=frappe.db.sql("select company,from_date,to_date,count(*) qty from `tabBudget Period` where status in ('Open','Closed') group by company,from_date,to_date having count(*)>1",as_dict=True)
    checks.append({"check":"No duplicate active period ranges","ok":not duplicate_periods,"details":duplicate_periods})
    missing_keys=frappe.db.count("Commitment Entry",{"event_key":["in",[None,""]]})
    checks.append({"check":"All commitment events have keys","ok":missing_keys==0,"details":{"missing":missing_keys}})
    duplicate_keys=frappe.db.sql("select parent,event_key,count(*) qty from `tabCommitment Entry` where coalesce(event_key,'')!='' group by parent,event_key having count(*)>1",as_dict=True)
    checks.append({"check":"No duplicate event keys per ledger","ok":not duplicate_keys,"details":duplicate_keys[:20]})
    pending_gl=frappe.db.count("Commitment Entry",{"stage":"Invoiced","direction":"Increase","matching_status":["in",["Pending GL","Partially Matched","Exception"]]})
    checks.append({"check":"GL matching queue is clear","ok":pending_gl==0,"details":{"pending_or_partial":pending_gl}})
    missing_period=frappe.db.count("Commitment Entry",{"stage":["in",["Requested","Reserved","Ordered","Contracted","Invoiced"]],"commitment_period":["in",[None,""]]})
    checks.append({"check":"All financial commitment events have periods","ok":missing_period==0,"details":{"missing":missing_period}})
    ambiguous=frappe.db.count("Budget Line",{"migration_status":"Review Required"})
    checks.append({"check":"Legacy migration review queue is empty","ok":ambiguous==0,"details":{"review_required":ambiguous}})
    unsynced=frappe.db.count("Budget Line",{"erpnext_sync_status":["in",["Not Synced","Review Required","Error"]]})
    checks.append({"check":"ERPNext Budget sync queue is clear","ok":unsynced==0,"details":{"pending_or_error":unsynced}})
    over=frappe.db.count("Budget Line",{"projection_status":"Over Budget"})
    checks.append({"check":"No over-budget projection exceptions","ok":over==0,"details":{"over_budget":over}})
    return {"ready":all(x["ok"] for x in checks),"checks":checks}
