import frappe
from .liabilities import validate_payment_dimensions

def _related_runs(doc):
    journals={x.reference_name for x in (doc.references or []) if x.reference_doctype=="Journal Entry" and x.reference_name}
    if not journals:return []
    return frappe.get_all("Payroll Allocation Run",filters={"journal_entry":["in",list(journals)],"docstatus":1},pluck="name",limit_page_length=0)
def validate_payment_entry(doc,method=None):validate_payment_dimensions(doc,method)
def payment_entry_on_submit(doc,method=None):validate_payment_dimensions(doc,method);_touch_runs(doc)
def payment_entry_on_cancel(doc,method=None):_touch_runs(doc)
def _touch_runs(doc):
    for run in _related_runs(doc):frappe.db.set_value("Payroll Allocation Run",run,{"payment_reconciliation_status":"Pending","reconciliation_status":"Pending"},update_modified=False)
