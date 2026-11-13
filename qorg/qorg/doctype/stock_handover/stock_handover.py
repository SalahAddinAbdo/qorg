import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt
from qorg.qorg.inventory_asset_custody.handover_service import populate_from_stock_entry, validate_handover
class StockHandover(Document):
 def before_validate(self): populate_from_stock_entry(self)
 def validate(self): validate_handover(self)
 def before_submit(self):
  if not self.recipient_signature: frappe.throw(_("Recipient Signature is required."))
 def on_submit(self): self.db_set("handover_status","Acknowledged" if self.fully_acknowledged else "Discrepancy Review")
 def on_cancel(self): self.db_set("handover_status","Cancelled")
