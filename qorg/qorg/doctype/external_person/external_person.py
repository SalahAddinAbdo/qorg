from __future__ import annotations

import frappe
from frappe.model.document import Document

from qorg.qorg.people_and_opportunities.services.people import update_profile_metrics, validate_external_person
from qorg.qorg.people_and_opportunities.web_form_services import validate_external_person_portal_access


class ExternalPerson(Document):
    def validate(self):
        validate_external_person(self)
        validate_external_person_portal_access(self)
        update_profile_metrics(self)

    def on_update(self):
        self.db_set("last_profile_update", frappe.utils.now(), update_modified=False)
