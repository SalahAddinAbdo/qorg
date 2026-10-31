import re
import frappe
from frappe.model.document import Document
class QOrgDesignSystemSettings(Document):
 def validate(self):
  for f in ("primary_color","secondary_color"):
   if not re.fullmatch(r"#[0-9A-Fa-f]{6}",(self.get(f) or "").strip()): frappe.throw(f"{f} must use #RRGGBB format.")
  if int(self.border_radius or 0) not in range(33): frappe.throw("Border Radius must be between 0 and 32 pixels.")
