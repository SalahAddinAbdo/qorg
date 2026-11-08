import frappe
from frappe import _


def get_context(context):
    if frappe.session.user == "Guest":
        frappe.throw(_("Login required"), frappe.PermissionError)
    context.no_cache = 1
    context.bids = frappe.get_all("Procurement Submission", filters={"owner": frappe.session.user}, fields=["name", "procurement_process", "procurement_notice", "submission_status", "submitted_at", "submission_version"], order_by="modified desc")
    notices = [row.procurement_notice for row in context.bids if row.procurement_notice]
    notice_map = {row.name: row for row in frappe.get_all("Procurement Notice", filters={"name": ["in", notices]}, fields=["name", "title", "route"])} if notices else {}
    for row in context.bids:
        notice = notice_map.get(row.procurement_notice)
        row.opportunity_title = notice.title if notice else None
        row.opportunity_route = notice.route if notice else None
    return context
