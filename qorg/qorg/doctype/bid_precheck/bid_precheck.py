from frappe.model.document import Document
from qorg.qorg.procurement_contracting.doctype_validators import validate_preliminary
class BidPrecheck(Document):
    def validate(self): validate_preliminary(self)
