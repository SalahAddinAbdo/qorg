from frappe.model.document import Document
from qorg.qorg.procurement_contracting.doctype_validators import validate_complaint
class ProcurementComplaint(Document):
    def validate(self): validate_complaint(self)
