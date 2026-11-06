import frappe
from frappe import _
from .permissions import financial_evaluation_has_permission


def assert_financial_file_access(file_url, procurement_submission, user=None):
    user = user or frappe.session.user
    submission = frappe.get_doc("Procurement Submission", procurement_submission)
    if file_url != submission.financial_proposal:
        return True
    probe = frappe._dict(procurement_process=submission.procurement_process)
    if not financial_evaluation_has_permission(probe, user=user, permission_type="read"):
        frappe.throw(_("Financial proposal access is not permitted at this stage."), frappe.PermissionError)
    return True

def has_file_permission(file_doc, user=None):
    user=user or frappe.session.user
    attached_to_doctype=getattr(file_doc,"attached_to_doctype",None)
    attached_to_name=getattr(file_doc,"attached_to_name",None)
    if attached_to_doctype != "Procurement Submission" or not attached_to_name:
        return None
    submission=frappe.get_doc("Procurement Submission",attached_to_name)
    if file_doc.file_url == submission.financial_proposal:
        probe=frappe._dict(procurement_process=submission.procurement_process)
        return bool(financial_evaluation_has_permission(probe,user=user,permission_type="read"))
    if submission.owner==user:
        return True
    probe=frappe._dict(procurement_process=submission.procurement_process)
    return bool(financial_evaluation_has_permission(probe,user=user,permission_type="read") or frappe.db.exists("Committee Member",{"user":user,"active":1,"recused":0}))
