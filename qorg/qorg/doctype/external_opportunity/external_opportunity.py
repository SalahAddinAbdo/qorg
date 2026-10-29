from frappe.model.document import Document

from qorg.qorg.people_and_opportunities.portal import (
    handle_external_opportunity_publication,
    validate_external_opportunity_publication,
)
from qorg.qorg.people_and_opportunities.services.opportunities import validate_opportunity


class ExternalOpportunity(Document):
    def validate(self):
        validate_opportunity(self)
        validate_external_opportunity_publication(self)

    def on_update(self):
        handle_external_opportunity_publication(self)
