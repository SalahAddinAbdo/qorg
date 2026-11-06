import json
import frappe
from frappe import _
from frappe.utils import now_datetime

PROFILE_ALLOWED_STATUSES = {"Approved"}

def validate_submission(doc, method=None):
    notice=frappe.get_doc("Procurement Notice",doc.procurement_notice) if doc.procurement_notice else None
    if notice and notice.deadline and now_datetime()>notice.deadline and doc.is_new():
        frappe.throw(_("Submission deadline has passed."))
    if not doc.supplier_registration:
        frappe.throw(_("An approved supplier profile is required before submitting a bid."))
    profile=frappe.get_doc("Supplier Registration",doc.supplier_registration)
    if profile.owner != frappe.session.user and "Procurement Manager" not in frappe.get_roles():
        frappe.throw(_("The supplier profile does not belong to the current portal user."),frappe.PermissionError)
    if profile.registration_status not in PROFILE_ALLOWED_STATUSES or not profile.supplier:
        frappe.throw(_("The supplier profile must be approved and linked to a Supplier before bid submission."))
    if profile.profile_locked == 0 and frappe.get_single_value("Procure Settings","lock_profile_after_approval"):
        frappe.throw(_("The approved supplier profile must be locked before bid submission."))
    if not doc.profile_current_confirmation:
        frappe.throw(_("Confirm that the supplier profile is complete and up to date for this submission."))
    if doc.supplier and doc.supplier != profile.supplier:
        frappe.throw(_("The bid Supplier must match the approved supplier profile."))
    doc.supplier=profile.supplier
    if doc.is_new() or not doc.profile_confirmation_on:
        doc.profile_confirmation_on=now_datetime()
        doc.profile_snapshot=json.dumps({"registration":profile.name,"supplier":profile.supplier,"legal_name":profile.legal_name,"status":profile.registration_status,"review_expiry_date":profile.review_expiry_date,"confirmed_by":frappe.session.user,"confirmed_on":str(doc.profile_confirmation_on)},sort_keys=True,default=str)
    if not doc.is_new():
        old=frappe.get_doc(doc.doctype,doc.name)
        if old.docstatus==1: frappe.throw(_("Submitted bids cannot be edited. Create a new version before the deadline."))
    duplicate=frappe.db.exists("Procurement Submission",{"procurement_process":doc.procurement_process,"supplier":doc.supplier,"docstatus":["<",2],"name":["!=",doc.name or ""]})
    if duplicate and not doc.get("supersedes_submission"):
        frappe.throw(_("A bid already exists for this supplier. Create a version that supersedes the previous bid."))

def withdraw_submission(name):
    doc=frappe.get_doc("Procurement Submission",name)
    if doc.owner!=frappe.session.user and "Procurement Manager" not in frappe.get_roles(): frappe.throw(_("Not permitted"),frappe.PermissionError)
    notice=frappe.get_doc("Procurement Notice",doc.procurement_notice)
    if now_datetime()>notice.deadline: frappe.throw(_("Bid cannot be withdrawn after the deadline."))
    doc.db_set("submission_status","Withdrawn"); return True
