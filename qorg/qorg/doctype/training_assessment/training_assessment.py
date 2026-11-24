from frappe.model.document import Document
from qorg.qorg.employee_lifecycle.training import validate_assessment
class TrainingAssessment(Document):
    def validate(self): validate_assessment(self)
