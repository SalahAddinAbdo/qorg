from frappe.model.document import Document
from qorg.qorg.employee_lifecycle.documents import validate_document_record, submit_document_record, cancel_document_record
class EmployeeDocumentRecord(Document):
    def validate(self): validate_document_record(self)
    def on_submit(self): submit_document_record(self)
    def on_cancel(self): cancel_document_record(self)
