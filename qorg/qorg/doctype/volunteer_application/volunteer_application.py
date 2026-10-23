from frappe.model.document import Document
from qorg.qorg.volunteering.services import validate_application
class VolunteerApplication(Document):
    def validate(self): validate_application(self)
