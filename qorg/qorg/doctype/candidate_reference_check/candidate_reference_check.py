from frappe.model.document import Document
from qorg.qorg.recruitment_extensions.reference_checks import validate_reference_check

class CandidateReferenceCheck(Document):
    def validate(self):
        validate_reference_check(self)
