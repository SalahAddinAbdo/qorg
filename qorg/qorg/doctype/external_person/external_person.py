from __future__ import annotations

import frappe
from frappe.model.document import Document

from qorg.qorg.people_and_opportunities.services.people import (
    update_profile_metrics,
    validate_external_person,
)


class ExternalPerson(Document):
    def validate(self):
        validate_external_person(self)
        update_profile_metrics(self)

    def on_update(self):
        self.db_set("last_profile_update", frappe.utils.now(), update_modified=False)
