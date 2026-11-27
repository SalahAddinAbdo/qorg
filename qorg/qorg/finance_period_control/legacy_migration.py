import frappe
from frappe.utils import flt, getdate
PATCH_ID="finance_period_control_phase_1d"

def execute(dry_run=False):
    summary={"periods_created":0,"lines_migrated":0,"review_required":0,"skipped":0}
    companies=frappe.get_all("Company",pluck="name")
    for company in companies:
        for fy in frappe.get_all("Fiscal Year",fields=["name","year_start_date","year_end_date"]):
            if not (fy.year_start_date and fy.year_end_date): continue
            code=f"{company}-{fy.name}"[:140]
            exists=frappe.db.exists("Budget Period",code)
            if not exists and not dry_run:
                frappe.get_doc({"doctype":"Budget Period","period_code":code,"period_name":f"{fy.name} - {company}","company":company,"from_date":fy.year_start_date,"to_date":fy.year_end_date,"fiscal_year":fy.name,"status":"Open","allow_commitments":1,"allow_actuals":1}).insert(ignore_permissions=True)
            if not exists: summary["periods_created"]+=1
    for name in frappe.get_all("Budget Line",pluck="name"):
        doc=frappe.get_doc("Budget Line",name)
        if doc.get("period_allocations"):
            summary["skipped"]+=1; continue
        amount=flt(doc.get("original_approved_amount") or doc.get("line_cost"))
        if not amount:
            if not dry_run: frappe.db.set_value("Budget Line",name,"migration_status","Review Required",update_modified=False)
            summary["review_required"]+=1; continue
        company=frappe.db.get_value("Project",doc.project,"company") if doc.project else None
        if not company:
            if not dry_run: frappe.db.set_value("Budget Line",name,"migration_status","Review Required",update_modified=False)
            summary["review_required"]+=1; continue
        project_period=doc.project and frappe.db.get_value("Project",doc.project,"qorg_default_budget_period")
        company_period=frappe.db.get_value("Company",company,"qorg_default_budget_period")
        candidate=project_period or company_period
        periods=frappe.get_all("Budget Period",filters={"company":company,"is_default":1,"status":["in",["Open","Closed"]]},fields=["name","from_date","to_date"])
        if candidate:
            periods=frappe.get_all("Budget Period",filters={"name":candidate,"company":company},fields=["name","from_date","to_date"])
        if len(periods)!=1:
            summary["review_required"]+=1
            if not dry_run: frappe.db.set_value("Budget Line",name,"migration_status","Review Required",update_modified=False)
            continue
        period=periods[0]
        if not dry_run:
            doc.append("period_allocations",{"budget_period":period.name,"allocated_amount":amount,"currency":doc.currency,"effective_from":period.from_date,"effective_to":period.to_date,"legacy_source":"Budget Line","legacy_key":name})
            doc.allocation_total=amount; doc.migration_status="Migrated"; doc.save(ignore_permissions=True)
        summary["lines_migrated"]+=1
    if not dry_run: frappe.db.commit()
    return summary
