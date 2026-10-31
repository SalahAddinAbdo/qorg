import frappe
from frappe.model.document import Document
from qorg.qorg.design_system.service import validate_values, clear_cache
class QOrgDesignSystemSettings(Document):
    def validate(self): validate_values(self)
    def on_update(self): clear_cache()
