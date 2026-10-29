from __future__ import annotations

from frappe.model.document import Document

from qorg.qorg.people_and_opportunities.portal import (
    handle_external_opportunity_publication,
    validate_external_opportunity_publication,
)
from qorg.qorg.people_and_opportunities.services.opportunities import (
    validate_opportunity,
)
from qorg.qorg.people_and_opportunities.web_form_services import (
    reconcile_opportunity_capacity,
)


class ExternalOpportunity(Document):
    def validate(self):
        validate_opportunity(self)
        validate_external_opportunity_publication(self)

    def on_update(self):
        handle_external_opportunity_publication(self)
        reconcile_opportunity_capacity(self.name)
