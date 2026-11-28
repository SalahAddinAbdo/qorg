from frappe.model.document import Document
from qorg.qorg.governance_accountability.risk_compliance import validate_compliance_obligation
class ComplianceObligation(Document):
    def validate(self): validate_compliance_obligation(self)
