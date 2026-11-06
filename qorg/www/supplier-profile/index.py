import frappe
from frappe import _
def get_context(context):
    if frappe.session.user == "Guest": frappe.throw(_("Login required"), frappe.PermissionError)
    context.no_cache=1
    context.profile=frappe.db.get_value("Supplier Registration", {"owner":frappe.session.user}, "name")
    return context
