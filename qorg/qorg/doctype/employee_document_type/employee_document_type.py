from frappe.model.document import Document
from qorg.qorg.employee_lifecycle.documents import validate_document_type
class EmployeeDocumentType(Document):
    def validate(self): validate_document_type(self)
