import frappe
from frappe.model.document import Document
from frappe.utils import getdate

class BudgetPeriodResolutionRule(Document):
    def validate(self):
        if self.valid_from and self.valid_to and getdate(self.valid_from) > getdate(self.valid_to):
            frappe.throw("Valid From cannot be after Valid To")
        period = frappe.get_doc("Budget Period", self.budget_period)
        if period.company != self.company:
            frappe.throw("Resolution rule and Budget Period must use the same Company")
