import frappe
from frappe import _
from frappe.utils import get_datetime, now_datetime


def get_context(context):
    route = frappe.form_dict.get("route")
    if not route:
        frappe.throw(_("Opportunity route is required"))
    context.notice = frappe.get_doc("Procurement Notice", {"route": route, "published": 1, "docstatus": 1})
    context.process = frappe.get_doc("Procurement Process", context.notice.procurement_process) if context.notice.procurement_process else None
    context.current_path = "/procurement-opportunity?route=" + route
    context.no_cache = 1
    closed = bool(context.notice.deadline and get_datetime(context.notice.deadline) <= now_datetime())
    context.action = "closed" if closed else "login"
    context.action_message = _("This opportunity is closed and no longer accepts submissions.") if closed else None
    context.submission_url = None
    if frappe.session.user != "Guest" and not closed:
        profile = frappe.db.get_value("Supplier Registration", {"owner": frappe.session.user}, ["name", "supplier", "registration_status", "profile_locked"], as_dict=True)
        if not profile:
            context.action = "profile"
            context.action_message = _("Create your supplier profile before submitting a bid.")
        else:
            existing = frappe.db.get_value("Procurement Submission", {"owner": frappe.session.user, "procurement_notice": context.notice.name, "submission_status": ["!=", "Withdrawn"]}, "name")
            if existing:
                context.action = "existing"
                context.submission_url = "/tender-submission?name=" + existing
                context.action_message = _("You already have a bid for this opportunity. Open it to review or update it.")
            else:
                context.action = "apply"
                context.submission_url = "/tender-submission?procurement_notice=" + context.notice.name
    return context
