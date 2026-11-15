import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate
from qorg.qorg.finance_budget_grants.currency import validate_agreement_currency

class FundingAgreement(Document):
    def validate(self):
        if getdate(self.start_date) > getdate(self.end_date):
            frappe.throw(_("Agreement Start Date cannot be after End Date."))
        if getdate(self.eligibility_start_date) > getdate(self.eligibility_end_date):
            frappe.throw(_("Eligibility Start Date cannot be after End Date."))
        if not 0 <= flt(self.flexibility_percent) <= 100:
            frappe.throw(_("Budget Flexibility must be between 0 and 100%."))
        validate_agreement_currency(self)
        total = sum(flt(row.amount) for row in self.installments)
        if total > flt(self.agreement_amount):
            frappe.throw(_("Funding installments exceed the agreement amount."))
        self._validate_weights()

    def _validate_weights(self):
        weighted = [row for row in self.budget_rules if row.is_active and flt(row.weight_percent)]
        if weighted:
            total = sum(flt(row.weight_percent) for row in weighted)
            if abs(total - 100) > 0.0001:
                frappe.throw(_("Budget Rule weights must total exactly 100%. Current total: {0}%. Difference: {1}%.").format(total, 100-total))

    def before_submit(self):
        if self.status not in ("Under Review", "Active"):
            frappe.throw(_("Funding Agreement can be submitted only from Under Review through the Activate workflow action."))

    def before_cancel(self):
        if self.status not in ("Active", "Suspended", "Closing"):
            frappe.throw(_("Only a submitted Funding Agreement can be cancelled."))

    def before_update_after_submit(self):
        if self.status not in ("Active", "Suspended", "Closing"):
            frappe.throw(_("Invalid submitted Funding Agreement status."))
