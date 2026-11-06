from frappe.model.document import Document
from qorg.qorg.procurement_contracting.doctype_validators import validate_framework
class FrameworkAgreement(Document):
    def validate(self): validate_framework(self)
