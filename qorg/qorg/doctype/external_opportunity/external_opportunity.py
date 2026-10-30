from __future__ import annotations

from frappe.model.document import Document
from frappe.utils import cint

from qorg.qorg.people_and_opportunities.services.opportunities import validate_opportunity


class ExternalOpportunity(Document):
    def validate(self):
        validate_opportunity(self)
        count = cint(self.get("application_count"))
        limit = cint(self.get("application_limit"))
        self.remaining_application_capacity = max(limit - count, 0) if limit > 0 else 0
