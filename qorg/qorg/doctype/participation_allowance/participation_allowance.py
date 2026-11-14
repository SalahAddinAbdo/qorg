import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

class ParticipationAllowance(Document):
    def validate(self):
        if flt(self.amount) < 0:
            frappe.throw(_("Allowance Amount cannot be negative."))
        if flt(self.approved_amount) < 0:
            frappe.throw(_("Approved Amount cannot be negative."))
        if flt(self.approved_amount) > flt(self.amount) and not (self.approval_remarks or "").strip():
            frappe.throw(_("Approval Remarks are required when Approved Amount exceeds Amount."))
        if self.status == "Approved" and not self.approved_by:
            self.approved_by = frappe.session.user
