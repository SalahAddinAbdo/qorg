from __future__ import annotations
import json,frappe
from frappe.utils import now_datetime
from qorg.qorg.cost_distribution.acceptance import audit_runtime_configuration

def run_runtime_acceptance():
    result=audit_runtime_configuration();result["generated_on"]=str(now_datetime());result["site"]=frappe.local.site
    path=frappe.get_site_path("private","files","qorg-cost-distribution-runtime-acceptance.json")
    with open(path,"w",encoding="utf-8") as handle:json.dump(result,handle,ensure_ascii=False,indent=2,default=str)
    if not result["passed"]:frappe.throw("Cost Distribution runtime configuration audit failed. Review the generated report.")
    return result
