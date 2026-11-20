import json,frappe
from frappe.utils import now_datetime
def migrate_nested_accrual_distributions():
 rows=frappe.get_all("Cost Distribution Row",filters={"parenttype":"Service and Allowance Accrual Line"},fields=["name","parent"],limit_page_length=0) if frappe.db.exists("DocType","Cost Distribution Row") else []
 report={"started_on":str(now_datetime()),"found":len(rows),"migrated":0,"missing_parent":[]}
 for row in rows:
  parent=frappe.db.get_value("Service and Allowance Accrual Line",row.parent,["parent","idx","service_item","expense_account","gross_amount","net_payable","custom_distribution_source_key"],as_dict=True)
  if not parent or not parent.parent:report["missing_parent"].append(row.name);continue
  key=parent.custom_distribution_source_key or frappe.generate_hash(length=20);frappe.db.set_value("Service and Allowance Accrual Line",row.parent,"custom_distribution_source_key",key,update_modified=False)
  frappe.db.set_value("Cost Distribution Row",row.name,{"parent":parent.parent,"parenttype":"Service and Allowance Accrual","parentfield":"cost_distributions","source_doctype":"Service and Allowance Accrual","source_child_doctype":"Service and Allowance Accrual Line","source_row":row.parent,"source_key":key,"source_row_idx":parent.idx,"source_item":parent.service_item,"source_account":parent.expense_account,"source_amount":parent.net_payable or parent.gross_amount},update_modified=False);report["migrated"]+=1
 report["finished_on"]=str(now_datetime());path=frappe.get_site_path("private","files","qorg-cost-distribution-migration-report.json")
 with open(path,"w",encoding="utf-8") as h:json.dump(report,h,ensure_ascii=False,indent=2)
 if report["missing_parent"]:frappe.throw("Cost Distribution migration has missing parent rows. Review qorg-cost-distribution-migration-report.json")
 return report
