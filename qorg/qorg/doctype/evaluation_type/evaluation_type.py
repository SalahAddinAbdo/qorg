from frappe.model.document import Document
from qorg.qorg.employee_lifecycle.performance import validate_evaluation_type
class EvaluationType(Document):
    def validate(self): validate_evaluation_type(self)
