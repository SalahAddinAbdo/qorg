from frappe.model.document import Document
from qorg.qorg.procurement_contracting.submission_service import validate_submission
class ProcurementSubmission(Document):
    def validate(self): validate_submission(self)
