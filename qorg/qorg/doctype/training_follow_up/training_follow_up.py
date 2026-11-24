from frappe.model.document import Document

from qorg.qorg.employee_lifecycle.training import validate_follow_up


class TrainingFollowup(Document):
    def validate(self):
        validate_follow_up(self)
