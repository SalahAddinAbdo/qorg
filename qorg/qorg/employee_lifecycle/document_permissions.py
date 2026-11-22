import frappe
SENSITIVE={"Highly Confidential","Restricted HR","Restricted Medical","Restricted Financial","Safeguarding Restricted"}
PRIVILEGED={"System Manager","HR Manager"}

def query_condition(user=None):
    user=user or frappe.session.user
    roles=set(frappe.get_roles(user))
    if user=="Administrator" or roles.intersection(PRIVILEGED): return ""
    employee=frappe.db.get_value("Employee",{"user_id":user},"name")
    if employee:
        return f"(`tabEmployee Document Record`.`subject_doctype`='Employee' and `tabEmployee Document Record`.`subject_name`={frappe.db.escape(employee)} and `tabEmployee Document Record`.`confidentiality_level` not in ('Restricted HR','Restricted Medical','Restricted Financial','Safeguarding Restricted'))"
    return "1=0"

def has_permission(doc,user=None,permission_type=None):
    user=user or frappe.session.user
    roles=set(frappe.get_roles(user))
    if user=="Administrator" or roles.intersection(PRIVILEGED): return None
    employee=frappe.db.get_value("Employee",{"user_id":user},"name")
    if doc.subject_doctype=="Employee" and doc.subject_name==employee and doc.confidentiality_level not in SENSITIVE:
        return permission_type in (None,"read","select","print")
    return False
