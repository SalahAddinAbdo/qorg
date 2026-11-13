import frappe
from frappe import _
from frappe.model.document import Document
from qorg.qorg.inventory_asset_custody.asset_control import validate_custody,sync_asset_custody
class AssetCustody(Document):
 def validate(self): validate_custody(self)
 def before_submit(self):
  if not self.recipient_declaration or not self.custodian_signature: frappe.throw(_("Recipient declaration and signature are required."))
 def on_submit(self): self.db_set("custody_status","Active");sync_asset_custody(self,True)
 def on_cancel(self): self.db_set("custody_status","Cancelled");sync_asset_custody(self,False)
