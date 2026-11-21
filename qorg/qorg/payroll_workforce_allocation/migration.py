import json,frappe
from frappe.utils import now_datetime
from .provisioning import provision_payroll_workforce_allocation
from .meta_audit import run_payroll_capability_audit
def _counts():
    return {dt:frappe.db.count(dt) for dt in ("Workforce Funding Plan","Payroll Cost Policy","Payroll Allocation Run","Monthly Effort Certification") if frappe.db.exists("DocType",dt)}
def migrate():
    before=_counts();provision_payroll_workforce_allocation();frappe.clear_cache();after=_counts();audit=run_payroll_capability_audit()
    report={"version":"3.0.2","generated_on":str(now_datetime()),"before":before,"after":after,"financial_backfill_performed":False,"capabilities":audit,"ready_for_staging":audit.get("ready_for_pilot",False),"ready_for_acceptance":False}
    path=frappe.get_site_path("private","files","qorg-payroll-workforce-migration-audit-v3.0.2.json")
    with open(path,"w",encoding="utf-8") as handle:json.dump(report,handle,indent=2,default=str)
    return report
