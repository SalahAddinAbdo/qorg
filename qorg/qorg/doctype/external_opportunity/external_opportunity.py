from frappe.model.document import Document
from qorg.qorg.people_and_opportunities.services.opportunities import validate_opportunity
class ExternalOpportunity(Document):
    def validate(self): validate_opportunity(self)
