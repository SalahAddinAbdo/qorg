from frappe.model.document import Document
from qorg.qorg.volunteer_management import services
class ParticipationEngagement(Document):
    def validate(self): services.validate_engagement(self)
