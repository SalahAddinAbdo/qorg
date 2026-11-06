import frappe
from frappe import _
def get_context(context):
    if frappe.session.user == "Guest": frappe.throw(_("Login required"), frappe.PermissionError)
    context.no_cache=1
    context.bids=frappe.get_all("Procurement Submission",filters={"owner":frappe.session.user},fields=["name","procurement_process","submission_status","submitted_at"],order_by="modified desc")
    return context
