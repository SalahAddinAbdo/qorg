from frappe.model.document import Document

from qorg.qorg.governance_accountability.validations import validate_accountability_case


class AccountabilityCase(Document):
    def validate(self):
        validate_accountability_case(self)
