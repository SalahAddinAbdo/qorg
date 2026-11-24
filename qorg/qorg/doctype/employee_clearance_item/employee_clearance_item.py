from __future__ import annotations
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime
class EmployeeClearanceItem(Document):
 def validate(self):
  complete=self.status in ("Completed","Exception Approved")
  if self.status=="Exception Approved":
   self.exception_approved=1
   if not (self.exception_reason or "").strip():frappe.throw(_("Exception Reason is required."))
   if not self.exception_approval_doctype or not self.exception_approval:frappe.throw(_("Exception Approval DocType and Document are required."))
  if self.outstanding_amount and not self.currency:frappe.throw(_("Currency is required when Outstanding Amount is set."))
  if complete and not self.completed_on:self.completed_on=now_datetime();self.completed_by=frappe.session.user
  if not complete:self.completed_on=None;self.completed_by=None
