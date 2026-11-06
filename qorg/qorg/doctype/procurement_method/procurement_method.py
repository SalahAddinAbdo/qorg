from frappe.model.document import Document
from qorg.qorg.procurement_contracting.doctype_validators import validate_method
class ProcurementMethod(Document):
    def validate(self): validate_method(self)
