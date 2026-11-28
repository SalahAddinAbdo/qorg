from frappe.model.document import Document
from qorg.qorg.governance_accountability.investigation import validate_investigation
class InvestigationCase(Document):
    def validate(self): validate_investigation(self)
