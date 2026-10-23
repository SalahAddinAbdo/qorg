import frappe
from frappe.model.document import Document


class ManagedConfigurationState(Document):
    def validate(self):
        if frappe.session.user != "Administrator" and not frappe.flags.in_install and not frappe.flags.in_migrate:
            frappe.throw("Only Administrator can modify managed configuration state.", frappe.PermissionError)
