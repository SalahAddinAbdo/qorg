import frappe
from frappe import _

LEGACY_DOCTYPE = "Procurement Contract"


def execute():
    """Remove the retired duplicate contract DocType after confirming it is empty."""
    if not frappe.db.exists("DocType", LEGACY_DOCTYPE):
        return
    count = frappe.db.count(LEGACY_DOCTYPE)
    if count:
        frappe.throw(_("Cannot remove {0}: {1} record(s) still exist.").format(LEGACY_DOCTYPE, count))
    frappe.delete_doc("DocType", LEGACY_DOCTYPE, force=True, ignore_permissions=True)
