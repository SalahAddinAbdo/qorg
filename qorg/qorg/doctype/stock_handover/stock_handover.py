import frappe
from frappe import _
from frappe.model.document import Document
from qorg.qorg.inventory_asset_custody.handover_service import populate_from_stock_entry, validate_handover, mark_confirmation


class StockHandover(Document):
    def before_validate(self):
        populate_from_stock_entry(self)

    def validate(self):
        validate_handover(self)

    def before_submit(self):
        if self.recipient_type == "Employee":
            return
        method = self.external_confirmation_method
        if method == "Direct Signature" and not self.recipient_signature:
            frappe.throw(_("External Recipient Signature is required."))
        if method == "Signed Document" and not self.evidence:
            frappe.throw(_("Signed handover document is required."))
        if method in {"Email Confirmation", "Witnessed Confirmation"} and not self.evidence:
            frappe.throw(_("Confirmation evidence is required for the selected external confirmation method."))

    def on_submit(self):
        mark_confirmation(self)
        self.db_set("handover_status", "Acknowledged" if self.fully_acknowledged else "Discrepancy Review")

    def on_cancel(self):
        self.db_set("handover_status", "Cancelled")
