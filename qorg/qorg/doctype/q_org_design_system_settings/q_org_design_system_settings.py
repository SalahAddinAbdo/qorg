import frappe
from frappe.model.document import Document
from qorg.qorg.design_system.service import clear_cache, sync_feature_control, validate_values

class QOrgDesignSystemSettings(Document):
    def validate(self):
        validate_values(self)

    def on_update(self):
        clear_cache()
        sync_feature_control(bool(self.enabled))
        frappe.publish_realtime("qorg_design_system_changed", {"settings_updated": True}, after_commit=True)
