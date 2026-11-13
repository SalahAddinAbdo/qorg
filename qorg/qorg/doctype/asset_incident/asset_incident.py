import frappe
from frappe import _
from frappe.model.document import Document
class AssetIncident(Document):
 def validate(self):
  if bool(self.item_code)==bool(self.asset): frappe.throw(_("Select either Item Code or Asset."))
  if self.decision=="Repair" and not self.asset: frappe.throw(_("Repair requires an Asset."))
 def before_submit(self):
  if self.decision=="Pending": frappe.throw(_("A decision is required."))
  if self.decision!="No Action" and not self.corrective_action: frappe.throw(_("Corrective Action is required."))
 def on_submit(self): self.db_set("incident_status","Resolved")
