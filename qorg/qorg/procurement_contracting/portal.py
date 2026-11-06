import frappe
from frappe import _
from frappe.utils import now_datetime

@frappe.whitelist(allow_guest=True)
def get_notice(route):
 notice=frappe.get_doc('Procurement Notice',{'route':route,'published':1,'docstatus':1}); return notice.as_dict()

@frappe.whitelist()
def submit_bid(notice,supplier,technical_proposal=None,financial_proposal=None,declaration=0):
 n=frappe.get_doc('Procurement Notice',notice)
 if not n.published or now_datetime()>n.deadline: frappe.throw(_('Submission deadline has passed'))
 if not declaration: frappe.throw(_('Declaration is required'))
 d=frappe.get_doc({'doctype':'Procurement Submission','procurement_process':n.procurement_process,'procurement_notice':n.name,'supplier':supplier,'technical_proposal':technical_proposal,'financial_proposal':financial_proposal,'declaration':1,'submission_status':'Submitted','submitted_at':now_datetime()})
 d.insert(); d.submit(); return d.name

@frappe.whitelist()
def request_supplier_profile_update(registration, reason):
    doc = frappe.get_doc("Supplier Registration", registration)
    if doc.owner != frappe.session.user:
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    if not frappe.get_single_value("Procurement and Contracting Settings", "allow_update_request_after_approval"):
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
