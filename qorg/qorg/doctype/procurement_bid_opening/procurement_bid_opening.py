from frappe.model.document import Document
from qorg.qorg.procurement_contracting.doctype_validators import validate_bid_opening
class ProcurementBidOpening(Document):
    def validate(self): validate_bid_opening(self)
