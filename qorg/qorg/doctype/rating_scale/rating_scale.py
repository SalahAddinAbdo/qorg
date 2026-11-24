from frappe.model.document import Document
from qorg.qorg.employee_lifecycle.performance import validate_rating_scale
class RatingScale(Document):
    def validate(self): validate_rating_scale(self)
