import frappe
from frappe.model.document import Document
from frappe.utils import now
from qorg.qorg.design_system import DESIGN_SYSTEM_SCHEMA_VERSION
from qorg.qorg.design_system.service import fingerprint, validate_values, values_from

class QOrgDesignPreset(Document):
    def validate(self):
        validate_values(self)
        self.schema_version = DESIGN_SYSTEM_SCHEMA_VERSION
        self.configuration_fingerprint = fingerprint(values_from(self, with_defaults=False))
        self.validation_status = "Valid"
        self.last_validated_on = now()
        if self.is_standard and not frappe.has_role("System Manager"):
            frappe.throw("Only System Manager can modify a standard preset.")
