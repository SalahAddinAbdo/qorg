from frappe.model.document import Document
from qorg.qorg.procurement_contracting.doctype_validators import validate_amendment
class ProcurementAmendment(Document):
    def validate(self): validate_amendment(self)
