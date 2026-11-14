from __future__ import annotations
import frappe

PRIVILEGED={"System Manager","Procurement Manager"}

def _allowed(user):
    return user=="Administrator" or bool(PRIVILEGED & set(frappe.get_roles(user)))

def query(user=None):
    user=user or frappe.session.user
    if _allowed(user): return ""
    return f"(`tabProcurement Complaint`.`owner`={frappe.db.escape(user)} or `tabProcurement Complaint`.`assigned_to`={frappe.db.escape(user)})"

def has(doc,user=None,permission_type=None):
    user=user or frappe.session.user
    if _allowed(user): return True
    in_scope=user in {doc.owner,doc.assigned_to}
    if permission_type in {None,"read","select","print","email","report"}: return in_scope
    if permission_type in {"write"}: return in_scope and doc.status not in {"Decision Issued","Closed"}
    if permission_type in {"create"}: return True
    return False
