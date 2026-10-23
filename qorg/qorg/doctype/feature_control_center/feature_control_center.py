import frappe
from frappe.model.document import Document

from qorg.qorg.enterprise_foundation.permissions import require_administrator


class FeatureControlCenter(Document):
    def before_load(self):
        require_administrator()

    def validate(self):
        require_administrator()

    def on_update(self):
        require_administrator()
