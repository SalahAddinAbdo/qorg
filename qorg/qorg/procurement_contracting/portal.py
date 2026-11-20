import frappe
from frappe import _
from frappe.utils import now_datetime

from qorg.qorg.procurement_contracting.settings import get_setting


PUBLIC_NOTICE_FIELDS = (
    "name",
    "procurement_process",
    "notice_type",
    "title",
    "route",
    "deadline",
    "summary",
    "documents",
)


def _get_published_notice(*, name=None, route=None):
    filters = {"published": 1, "docstatus": 1}
    if name:
        filters["name"] = name
    elif route:
        filters["route"] = route
    else:
        frappe.throw(_("A procurement notice is required."))

    notice = frappe.db.get_value(
        "Procurement Notice",
        filters,
        PUBLIC_NOTICE_FIELDS,
        as_dict=True,
    )
    if not notice:
        frappe.throw(_("Procurement notice not found."), frappe.DoesNotExistError)
    return notice


@frappe.whitelist(allow_guest=True)
def get_notice(route):
    """Return only fields explicitly approved for a published notice."""
    return _get_published_notice(route=route)


@frappe.whitelist()
def submit_bid(
    notice,
    supplier,
    technical_proposal=None,
    financial_proposal=None,
    declaration=0,
):
    if frappe.session.user == "Guest":
        frappe.throw(_("Please sign in to submit a bid."), frappe.PermissionError)

    published_notice = _get_published_notice(name=notice)
    if not published_notice.deadline or now_datetime() > published_notice.deadline:
        frappe.throw(_("Submission deadline has passed."))
    if not frappe.utils.cint(declaration):
        frappe.throw(_("Declaration is required."))

    registration = frappe.db.get_value(
        "Supplier Registration",
        {
            "owner": frappe.session.user,
            "supplier": supplier,
            "registration_status": "Approved",
            "docstatus": 1,
        },
        "name",
    )
    if not registration:
        frappe.throw(
            _("An approved supplier profile belonging to the current user is required."),
            frappe.PermissionError,
        )

    submission = frappe.get_doc(
        {
            "doctype": "Procurement Submission",
            "procurement_process": published_notice.procurement_process,
            "procurement_notice": published_notice.name,
            "supplier_registration": registration,
            "supplier": supplier,
            "technical_proposal": technical_proposal,
            "financial_proposal": financial_proposal,
            "declaration": 1,
            "profile_current_confirmation": 1,
            "submission_status": "Submitted",
            "submitted_at": now_datetime(),
        }
    )
    submission.insert()
    submission.submit()
    return submission.name


@frappe.whitelist()
def request_supplier_profile_update(registration, reason):
    doc = frappe.get_doc("Supplier Registration", registration)
    if doc.owner != frappe.session.user:
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    if not get_setting( "allow_update_request_after_approval"):
        frappe.throw(_("Supplier profile update requests are disabled."))
    doc.db_set("update_requested", 1)
    doc.add_comment("Comment", _("Supplier requested a profile update: {0}").format(reason))
    return True

@frappe.whitelist()
def create_bid_version(submission):
    old = frappe.get_doc("Procurement Submission", submission)
    if old.owner != frappe.session.user:
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    notice = frappe.get_doc("Procurement Notice", old.procurement_notice)
    if now_datetime() > notice.deadline:
        frappe.throw(_("Submission deadline has passed."))
    new = frappe.copy_doc(old)
    new.docstatus = 0
    new.submission_status = "Draft"
    new.submitted_at = None
    new.submission_version = (old.submission_version or 1) + 1
    new.supersedes_submission = old.name
    new.insert()
    return new.name

@frappe.whitelist()
def withdraw_bid(submission, reason=None):
    from qorg.qorg.procurement_contracting.submission_service import withdraw_submission
    result = withdraw_submission(submission)
    if reason:
        frappe.db.set_value("Procurement Submission", submission, "withdrawal_reason", reason)
    frappe.db.set_value("Procurement Submission", submission, "withdrawn_on", now_datetime())
    return result

@frappe.whitelist()
def respond_to_clarification(name, response):
    doc = frappe.get_doc("Procurement Clarification", name)
    if doc.owner != frappe.session.user:
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    doc.response = response
    doc.responded_on = now_datetime()
    doc.save()
    return True

@frappe.whitelist()
def get_supplier_profile():
    if frappe.session.user == "Guest":
        frappe.throw(_("Login required"), frappe.PermissionError)
    name=frappe.db.get_value("Supplier Registration",{"owner":frappe.session.user},"name")
    return frappe.get_doc("Supplier Registration",name).as_dict() if name else None

@frappe.whitelist()
def get_my_bids():
    if frappe.session.user == "Guest": frappe.throw(_("Login required"),frappe.PermissionError)
    return frappe.get_all("Procurement Submission",filters={"owner":frappe.session.user},fields=["name","procurement_process","procurement_notice","submission_status","submission_version","submitted_at","supersedes_submission"],order_by="modified desc")
