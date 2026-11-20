import frappe
from frappe import _

def validate_generated_journal(doc, method=None):
    meta=frappe.get_meta("Journal Entry")
    source_type=doc.get("custom_qorg_source_doctype") if meta.has_field("custom_qorg_source_doctype") else None
    source_name=doc.get("custom_qorg_source_name") if meta.has_field("custom_qorg_source_name") else None
    source_hash=doc.get("custom_qorg_source_hash") if meta.has_field("custom_qorg_source_hash") else None
    if source_type != "Service and Allowance Accrual" or not source_name:return
    source=frappe.get_doc(source_type,source_name)
    current=source.get_source_hash()
    if source_hash != current: frappe.throw(_("The source accrual changed after this Journal Entry was generated. Regenerate the draft entry before submission."))

def on_submit_generated_journal(doc, method=None):
    if doc.get("custom_qorg_source_doctype") == "Service and Allowance Accrual" and doc.get("custom_qorg_source_name"):
        frappe.db.set_value("Service and Allowance Accrual",doc.custom_qorg_source_name,{"operational_status":"Posted"},update_modified=False)
    run=frappe.db.get_value("Shared Cost Allocation Run",{"journal_entry":doc.name},"name")
    if run: frappe.db.set_value("Shared Cost Allocation Run",run,{"run_status":"Posted","reconciliation_status":"Matched"},update_modified=False)

def on_cancel_generated_journal(doc, method=None):
    if doc.get("custom_qorg_source_doctype") == "Service and Allowance Accrual" and doc.get("custom_qorg_source_name"):
        frappe.db.set_value("Service and Allowance Accrual",doc.custom_qorg_source_name,{"operational_status":"Approved"},update_modified=False)
    run=frappe.db.get_value("Shared Cost Allocation Run",{"journal_entry":doc.name},"name")
    if run: frappe.db.set_value("Shared Cost Allocation Run",run,{"run_status":"Approved","reconciliation_status":"Pending"},update_modified=False)
