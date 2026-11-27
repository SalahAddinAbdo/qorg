import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

from qorg.qorg.volunteer_management import services


class ParticipationServiceLog(Document):
    def validate(self):
        services.validate_service_log(self)
        if self.status == "Verified" and not self.verified_by:
            self.verified_by = frappe.session.user
            self.verified_on = now_datetime()

    def on_update(self):
        services.update_verified_hours(self.engagement)

    def after_delete(self):
        services.update_verified_hours(self.engagement)
