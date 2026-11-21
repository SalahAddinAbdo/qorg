import frappe
from frappe.model.document import Document
from qorg.qorg.payroll_workforce_allocation.component_policy import validate_policy, activate_policy, cancel_policy
class PayrollCostPolicy(Document):
    def validate(self): validate_policy(self)
    def on_submit(self): activate_policy(self)
    def on_cancel(self): cancel_policy(self)
