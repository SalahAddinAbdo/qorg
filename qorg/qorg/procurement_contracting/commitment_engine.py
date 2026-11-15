import frappe
from frappe.utils import flt, nowdate
STAGES={"Requested":"requested","Reserved":"reserved","Ordered":"ordered","Contracted":"contracted","Accepted":"accepted","Invoiced":"invoiced","Paid":"paid"}


def _single_budget_line(material_request):
    if not material_request:
        return None
    meta = frappe.get_meta("Material Request Item")
    if not meta.has_field("budget_line"):
        return None
    values = frappe.get_all("Material Request Item", filters={"parent": material_request, "parenttype": "Material Request"}, pluck="budget_line")
    values = {value for value in values if value}
    return next(iter(values)) if len(values) == 1 else None

def rebuild_ledger(doc):
    totals={v:0 for v in STAGES.values()}
    for row in doc.entries:
        field=STAGES.get(row.stage)
        if field: totals[field]+=flt(row.amount)*(1 if row.direction=="Increase" else -1)
    for field,value in totals.items(): doc.set(field,value)

def record(process,stage,reference_doctype,reference_name,amount,direction="Increase",remarks=None, budget_line=None):
    name=frappe.db.get_value("Commitment Ledger",{"procurement_process":process})
    ledger=frappe.get_doc("Commitment Ledger",name) if name else frappe.new_doc("Commitment Ledger")
    if not name:
        p=frappe.get_doc("Procurement Process",process); ledger.update({"company":p.company,"project":p.project,"currency":p.currency,"procurement_process":p.name,"material_request":p.material_request,"budget_line":budget_line or _single_budget_line(p.material_request)})
    if budget_line and not ledger.get("budget_line"):
        ledger.budget_line = budget_line
    if frappe.db.exists("Commitment Entry",{"parent":ledger.name,"reference_doctype":reference_doctype,"reference_name":reference_name,"stage":stage,"direction":direction}): return ledger.name
    ledger.append("entries",{"stage":stage,"posting_date":nowdate(),"reference_doctype":reference_doctype,"reference_name":reference_name,"amount":amount,"direction":direction,"remarks":remarks})
    rebuild_ledger(ledger); ledger.save(ignore_permissions=True); return ledger.name
