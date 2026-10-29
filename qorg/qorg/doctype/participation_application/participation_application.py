from frappe.model.document import Document

from qorg.qorg.people_and_opportunities.web_form_services import (
    reconcile_participation_application_capacity,
    validate_participation_application_portal,
)
from qorg.qorg.volunteer_management import services


class ParticipationApplication(Document):
    def validate(self):
        validate_participation_application_portal(self)
        services.validate_application(self)

    def after_insert(self):
        reconcile_participation_application_capacity(self)

    def on_update(self):
        reconcile_participation_application_capacity(self)

    def on_cancel(self):
        reconcile_participation_application_capacity(self)

    def on_trash(self):
        reconcile_participation_application_capacity(self)
