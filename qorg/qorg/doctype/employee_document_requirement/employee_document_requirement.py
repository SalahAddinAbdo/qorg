from frappe.model.document import Document
from qorg.qorg.employee_lifecycle.documents import validate_document_requirement
class EmployeeDocumentRequirement(Document):
    def validate(self): validate_document_requirement(self)
