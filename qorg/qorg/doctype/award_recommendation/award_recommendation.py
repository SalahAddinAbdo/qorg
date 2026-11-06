from frappe.model.document import Document
from qorg.qorg.procurement_contracting.doctype_validators import validate_award_recommendation
class AwardRecommendation(Document):
    def validate(self): validate_award_recommendation(self)
