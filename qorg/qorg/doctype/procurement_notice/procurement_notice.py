from frappe.model.document import Document
from qorg.qorg.procurement_contracting.doctype_validators import validate_notice
class ProcurementNotice(Document):
    def validate(self): validate_notice(self)
