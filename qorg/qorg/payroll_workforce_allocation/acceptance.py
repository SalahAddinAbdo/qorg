import json,frappe
from frappe.utils import now_datetime
from .compatibility import validate_runtime
from .meta_audit import run_payroll_capability_audit
from .permissions import PRIVILEGED,READ_ONLY,AGGREGATE_ROLES
def _write(name,data):
    path=frappe.get_site_path("private","files",name)
    with open(path,"w",encoding="utf-8") as handle:json.dump(data,handle,indent=2,default=str)
    return path
def metadata_snapshot():
    doctypes=("Workforce Funding Plan","Workforce Funding Destination","Payroll Cost Policy","Payroll Component Rule","Payroll Liability Rule","Payroll Allocation Run","Payroll Allocation Result","Payroll Allocation Exception","Monthly Effort Certification","Monthly Effort Certification Detail","Payroll Reconciliation Detail")
    return {dt:{"exists":bool(frappe.db.exists("DocType",dt)),"modified":str(frappe.db.get_value("DocType",dt,"modified")) if frappe.db.exists("DocType",dt) else None,"fields":frappe.db.count("DocField",{"parent":dt}) if frappe.db.exists("DocType",dt) else 0} for dt in doctypes}
@frappe.whitelist()
def run_acceptance():
    frappe.only_for("System Manager");issues=validate_runtime();cap=run_payroll_capability_audit();snapshot=metadata_snapshot()
    result={"version":"3.0.2","generated_on":str(now_datetime()),"runtime_issues":issues,"capabilities":cap,"metadata":snapshot,"static_passed":True,"metadata_passed":all(x["exists"] for x in snapshot.values()),"runtime_passed":not issues and cap.get("ready_for_pilot",False),"accounting_passed":False,"budget_control_passed":False,"liability_passed":False,"payment_reconciliation_passed":False,"permissions_passed":False,"privacy_passed":False,"reports_passed":False,"print_passed":False,"fresh_install_passed":False,"upgrade_passed":False,"idempotency_passed":False,"ready_for_acceptance":False}
    _write("qorg-payroll-workforce-runtime-acceptance-v3.0.2.json",result);return result
@frappe.whitelist()
def capture_idempotency_snapshot(label="current"):
    frappe.only_for("System Manager");data={"version":"3.0.2","label":label,"generated_on":str(now_datetime()),"metadata":metadata_snapshot(),"custom_fields":frappe.get_all("Custom Field",filters={"module":"QOrg","fieldname":["like","custom_payroll%"]},fields=["name","modified","fieldtype","options","insert_after"],order_by="name",limit_page_length=0)};_write(f"qorg-payroll-workforce-idempotency-{label}.json",data);return data
