import frappe
from frappe import _
from frappe.model.document import Document
from qorg.qorg.inventory_asset_custody.verification_service import validate_verification
class PhysicalVerification(Document):
 def validate(self): validate_verification(self)
 def before_submit(self):
  if not self.snapshot_locked: frappe.throw(_("Snapshot must be locked before submission."))
  if self.recount_required: frappe.throw(_("Complete required recount before submission."))
