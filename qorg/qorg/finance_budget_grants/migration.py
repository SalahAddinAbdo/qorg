from __future__ import annotations
import frappe
from frappe.utils import flt
OLD_TEMPLATES=("Funding Agreement Review Required","Funding Agreement Activated","Funding Installment Due","Funding Report Due","Funding Agreement Closeout Required")
OLD_NOTIFICATIONS=("Finance - Funding Agreement Review Required","Finance - Funding Agreement Closeout Required")
def migrate_finance_budget_grants_v151(): return migrate_finance_budget_grants_v153()
def migrate_finance_budget_grants_v153():
 result={"budget_lines":0,"disabled_notifications":[],"retained_templates":[]}
 if frappe.db.exists("DocType","Budget Line"):
  meta=frappe.get_meta("Budget Line"); fields={x.fieldname for x in meta.fields}
  query=["name","line_cost"]+[x for x in ("original_approved_amount","current_approved_amount") if x in fields]
  for row in frappe.get_all("Budget Line",fields=query,limit_page_length=0):
   current=flt(row.get("line_cost")); values={}
   if "original_approved_amount" in fields and not flt(row.get("original_approved_amount")): values["original_approved_amount"]=current
   if "current_approved_amount" in fields and flt(row.get("current_approved_amount"))!=current: values["current_approved_amount"]=current
   if values: frappe.db.set_value("Budget Line",row.name,values,update_modified=False); result["budget_lines"]+=1
 for name in OLD_NOTIFICATIONS:
  if frappe.db.exists("Notification",name): frappe.db.set_value("Notification",name,"enabled",0,update_modified=False); result["disabled_notifications"].append(name)
 for name in OLD_TEMPLATES:
  if frappe.db.exists("Email Template",name): result["retained_templates"].append(name)
 return result

def migrate_finance_budget_grants_v154():
    result = migrate_finance_budget_grants_v153()
    if frappe.db.exists("Report", "Grant Closeout Status"):
        frappe.db.set_value("Report", "Grant Closeout Status", "disabled", 1, update_modified=False)
        result["disabled_report"] = "Grant Closeout Status"
    return result

def migrate_finance_budget_grants_v155():
    result = migrate_finance_budget_grants_v154()
    result["commitment_ledgers_backfilled"] = 0
    if frappe.db.exists("DocType", "Commitment Ledger") and frappe.get_meta("Commitment Ledger").has_field("budget_line"):
        for row in frappe.get_all("Commitment Ledger", filters={"budget_line": ["is", "not set"]}, fields=["name", "material_request"]):
            if not row.material_request or not frappe.db.exists("Material Request", row.material_request):
                continue
            item_meta = frappe.get_meta("Material Request Item")
            if not item_meta.has_field("budget_line"):
                continue
            values = frappe.get_all("Material Request Item", filters={"parent": row.material_request, "parenttype": "Material Request"}, pluck="budget_line")
            values = {value for value in values if value}
            if len(values) == 1:
                frappe.db.set_value("Commitment Ledger", row.name, "budget_line", next(iter(values)), update_modified=False)
                result["commitment_ledgers_backfilled"] += 1
    return result

def migrate_finance_budget_grants_v156():
    return migrate_finance_budget_grants_v155()
