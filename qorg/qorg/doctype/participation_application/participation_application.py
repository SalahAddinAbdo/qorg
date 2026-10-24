from frappe.model.document import Document
from qorg.qorg.volunteer_management import services
class ParticipationApplication(Document):
    def validate(self): services.validate_application(self)
