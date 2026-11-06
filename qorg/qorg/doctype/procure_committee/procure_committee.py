from frappe.model.document import Document
from qorg.qorg.procurement_contracting.doctype_validators import validate_committee
class ProcureCommittee(Document):
    def validate(self): validate_committee(self)
