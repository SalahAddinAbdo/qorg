import frappe
from frappe.model.document import Document
from qorg.qorg.procurement_contracting.submission_service import validate_submission
class ProcurementSubmission(Document):
    def validate(self): validate_submission(self)

    def onload(self):
        if self.procurement_process:
            self.set_onload("procurement_process_status", frappe.db.get_value("Procurement Process", self.procurement_process, "status"))
