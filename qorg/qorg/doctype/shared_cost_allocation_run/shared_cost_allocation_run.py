import frappe
from frappe.model.document import Document
from qorg.qorg.shared_cost_allocation.engine import preview_run, post_run, reverse_run

class SharedCostAllocationRun(Document):
    def validate(self):
        preview_run(self)

    def on_submit(self):
        post_run(self)

    def on_cancel(self):
        reverse_run(self)
