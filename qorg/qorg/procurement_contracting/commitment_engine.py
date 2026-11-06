import frappe
from frappe.utils import flt, nowdate
STAGES={"Requested":"requested","Reserved":"reserved","Ordered":"ordered","Contracted":"contracted","Accepted":"accepted","Invoiced":"invoiced","Paid":"paid"}
def rebuild_ledger(doc):
    totals={v:0 for v in STAGES.values()}
    for row in doc.entries:
        field=STAGES.get(row.stage)
        if field: totals[field]+=flt(row.amount)*(1 if row.direction=="Increase" else -1)
    for field,value in totals.items(): doc.set(field,value)

def record(process,stage,reference_doctype,reference_name,amount,direction="Increase",remarks=None):
    name=frappe.db.get_value("Procurement Commitment Ledger",{"procurement_process":process})
    ledger=frappe.get_doc("Procurement Commitment Ledger",name) if name else frappe.new_doc("Procurement Commitment Ledger")
    if not name:
        p=frappe.get_doc("Procurement Process",process); ledger.update({"company":p.company,"project":p.project,"currency":p.currency,"procurement_process":p.name,"material_request":p.material_request})
    if frappe.db.exists("Procurement Commitment Entry",{"parent":ledger.name,"reference_doctype":reference_doctype,"reference_name":reference_name,"stage":stage,"direction":direction}): return ledger.name
    ledger.append("entries",{"stage":stage,"posting_date":nowdate(),"reference_doctype":reference_doctype,"reference_name":reference_name,"amount":amount,"direction":direction,"remarks":remarks})
    rebuild_ledger(ledger); ledger.save(ignore_permissions=True); return ledger.name
