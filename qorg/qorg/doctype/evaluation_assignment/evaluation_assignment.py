from frappe.model.document import Document
from qorg.qorg.employee_lifecycle.performance import validate_assignment
class EvaluationAssignment(Document):
    def validate(self): validate_assignment(self)
