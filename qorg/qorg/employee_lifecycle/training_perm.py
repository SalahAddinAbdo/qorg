import frappe
HR={"HR Manager","HR User","System Manager"}

def assessment_query(user=None):
    user=user or frappe.session.user
    if user=="Administrator" or HR.intersection(frappe.get_roles(user)): return ""
    employee=frappe.db.get_value("Employee",{"user_id":user},"name")
    return f"(`tabTraining Assessment`.`assessor`={frappe.db.escape(user)}" + (f" or `tabTraining Assessment`.`employee`={frappe.db.escape(employee)})" if employee else ")")

def assessment_has_permission(doc,user=None,permission_type=None):
    user=user or frappe.session.user
    if user=="Administrator" or HR.intersection(frappe.get_roles(user)): return None
    employee=frappe.db.get_value("Employee",{"user_id":user},"name")
    if doc.assessor!=user and doc.employee!=employee:return False
    if permission_type in (None,"read","select","print","email"):return True
    return doc.assessor==user and doc.status=="Draft"

def follow_up_query(user=None):
    user=user or frappe.session.user
    if user=="Administrator" or HR.intersection(frappe.get_roles(user)): return ""
    employee=frappe.db.get_value("Employee",{"user_id":user},"name")
    parts=[f"`tabTraining Follow-up`.`responsible_user`={frappe.db.escape(user)}"]
    if employee:parts.append(f"`tabTraining Follow-up`.`employee`={frappe.db.escape(employee)}")
    return "("+" or ".join(parts)+")"

def follow_up_has_permission(doc,user=None,permission_type=None):
    user=user or frappe.session.user
    if user=="Administrator" or HR.intersection(frappe.get_roles(user)): return None
    employee=frappe.db.get_value("Employee",{"user_id":user},"name")
    if doc.responsible_user!=user and doc.employee!=employee:return False
    if permission_type in (None,"read","select","print","email"):return True
    return doc.responsible_user==user and doc.status not in {"Completed","Cancelled"}
