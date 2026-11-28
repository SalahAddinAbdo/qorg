from frappe.model.document import Document
from qorg.qorg.governance_accountability.investigation import validate_corrective_action
class CorrectiveAction(Document):
    def validate(self): validate_corrective_action(self)
