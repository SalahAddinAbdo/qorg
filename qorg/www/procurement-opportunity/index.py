from urllib.parse import quote

import frappe
from frappe import _
from frappe.utils import get_datetime, now_datetime


def get_context(context):
    route = (frappe.form_dict.get("route") or "").strip()
    if not route:
        frappe.throw(_("Opportunity route is required"))
    context.notice = frappe.get_doc(
        "Procurement Notice", {"route": route, "published": 1, "docstatus": 1}
    )
    context.process = frappe.get_doc(
        "Procurement Process", context.notice.procurement_process
    ) if context.notice.procurement_process else None
    context.no_cache = 1
    context.is_guest = frappe.session.user == "Guest"
    context.closed = bool(
        context.notice.deadline and get_datetime(context.notice.deadline) <= now_datetime()
    )
    if context.is_guest:
        context.action = "login"
        context.action_url = f"/login?redirect-to={quote('/procurement-opportunity?route=' + route, safe='')}"
    elif context.closed:
        context.action = "closed"
        context.action_url = None
    else:
        profile = frappe.db.get_value("Supplier Registration", {"owner": frappe.session.user}, "name")
        context.action = "apply" if profile else "profile"
        context.action_url = (
            "/api/method/qorg.qorg.procurement_contracting.portal_workflow.start_tender_submission"
            f"?route={quote(route, safe='')}"
            if profile
            else "/supplier-profile"
        )
    return context
