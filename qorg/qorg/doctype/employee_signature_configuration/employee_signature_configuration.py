from __future__ import annotations

from frappe.model.document import Document
from qorg.qorg.signatures.provisioning import validate_configuration, provision_signature_fields


class EmployeeSignatureConfiguration(Document):
    def validate(self):
        validate_configuration(self)

    def on_update(self):
        if self.enabled:
            provision_signature_fields(self)
