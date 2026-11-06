from frappe.model.document import Document
from qorg.qorg.procurement_contracting.doctype_validators import validate_clarification
class ProcurementClarification(Document):
    def validate(self): validate_clarification(self)
