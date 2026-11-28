from frappe.model.document import Document
from qorg.qorg.governance_accountability.risk_compliance import validate_enterprise_risk
class EnterpriseRisk(Document):
    def validate(self): validate_enterprise_risk(self)
