import frappe
from frappe import _
def get_context(context):
    route=frappe.form_dict.get("route")
    if not route: frappe.throw(_("Opportunity route is required"))
    context.notice=frappe.get_doc("Procurement Notice",{"route":route,"published":1,"docstatus":1})
    context.no_cache=1
    return context
