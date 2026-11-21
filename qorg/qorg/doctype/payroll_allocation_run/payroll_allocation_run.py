import frappe
from frappe.model.document import Document
from qorg.qorg.payroll_workforce_allocation.lifecycle import validate_run, submit_run, cancel_run
class PayrollAllocationRun(Document):
    def validate(self): validate_run(self)
    def on_submit(self): submit_run(self)
    def on_cancel(self): cancel_run(self)
    def on_trash(self):
        if self.docstatus or self.journal_entry or self.commitment_references: frappe.throw("Only an unused draft Payroll Allocation Run can be deleted.")
