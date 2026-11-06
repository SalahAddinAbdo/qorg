from frappe.model.document import Document
from qorg.qorg.procurement_contracting.contract_engine import validate_acceptance
class ProcureAcceptance(Document):
    def validate(self): validate_acceptance(self)
