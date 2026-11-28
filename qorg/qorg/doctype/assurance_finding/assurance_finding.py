from frappe.model.document import Document
from qorg.qorg.governance_accountability.risk_compliance import validate_assurance_finding
class AssuranceFinding(Document):
    def validate(self): validate_assurance_finding(self)
