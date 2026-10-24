from frappe.model.document import Document
from qorg.qorg.volunteer_management import services
class ParticipationAssessment(Document):
    def validate(self): services.validate_assessment(self)
    def on_update(self): services.recalculate_application(self.application)
    def on_cancel(self): services.recalculate_application(self.application)
    def on_trash(self): services.recalculate_application(self.application)
