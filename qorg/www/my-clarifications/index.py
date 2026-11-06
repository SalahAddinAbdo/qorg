import frappe
from frappe import _
def get_context(context):
    if frappe.session.user == "Guest": frappe.throw(_("Login required"), frappe.PermissionError)
    context.items=frappe.get_all("Procurement Clarification",filters={"owner":frappe.session.user},fields=["name","procurement_process","subject","due_date","responded_on"],order_by="modified desc")
    return context
