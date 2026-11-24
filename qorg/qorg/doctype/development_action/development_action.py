from frappe.model.document import Document
from qorg.qorg.employee_lifecycle.learning import validate_development_action
class DevelopmentAction(Document):
    def validate(self): validate_development_action(self)
