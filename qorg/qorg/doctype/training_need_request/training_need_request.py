from frappe.model.document import Document
from qorg.qorg.employee_lifecycle.learning import validate_training_need
class TrainingNeedRequest(Document):
    def validate(self): validate_training_need(self)
