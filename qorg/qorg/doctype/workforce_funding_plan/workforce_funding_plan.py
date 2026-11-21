import frappe
from frappe.model.document import Document
from qorg.qorg.payroll_workforce_allocation.funding_plan import validate_plan, activate_plan, cancel_plan
class WorkforceFundingPlan(Document):
    def validate(self): validate_plan(self)
    def on_submit(self): activate_plan(self)
    def on_cancel(self): cancel_plan(self)
