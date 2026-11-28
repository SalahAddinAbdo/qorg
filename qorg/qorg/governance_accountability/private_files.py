from __future__ import annotations
import hashlib
import frappe
from frappe import _
PROTECTED_DOCTYPES={"Accountability Case","Investigation Case","Corrective Action","Enterprise Risk","Compliance Obligation","Assurance Finding"}
def has_file_permission(file_doc,user=None):
    user=user or frappe.session.user
    if file_doc.attached_to_doctype not in PROTECTED_DOCTYPES or not file_doc.attached_to_name:return None
    return bool(frappe.has_permission(file_doc.attached_to_doctype,"read",file_doc.attached_to_name,user=user))
def validate_private_file(doc,method=None):
    if doc.attached_to_doctype not in PROTECTED_DOCTYPES or not doc.attached_to_name:return
    settings=frappe.get_single('Accountability Settings')
    if settings.force_private_attachments:doc.is_private=1
    old=doc.get_doc_before_save()
    if old and (old.attached_to_doctype,old.attached_to_name)!=(doc.attached_to_doctype,doc.attached_to_name):
        for dt,name in ((old.attached_to_doctype,old.attached_to_name),(doc.attached_to_doctype,doc.attached_to_name)):
            if dt and name and not frappe.has_permission(dt,"write",name):frappe.throw(_("Write permission is required on both records to move a protected attachment."),frappe.PermissionError)
def content_hash(file_name):
    file_doc=frappe.get_doc('File',file_name)
    content=file_doc.get_content()
    if isinstance(content,str):content=content.encode()
    return hashlib.sha256(content).hexdigest()
