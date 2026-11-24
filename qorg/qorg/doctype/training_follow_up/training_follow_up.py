from frappe.model.document import Document
from qorg.qorg.employee_lifecycle.training import validate_follow_up
class TrainingFollowUp(Document):
    def validate(self): validate_follow_up(self)
