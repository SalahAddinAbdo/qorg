import frappe
HR={"HR Manager","HR User","System Manager"}

def assignment_query(user=None):
    user=user or frappe.session.user
    if user=="Administrator" or HR.intersection(frappe.get_roles(user)):return ""
    employee=frappe.db.get_value("Employee",{"user_id":user},"name")
    if not employee:return "1=0"
    return f"(`tabEvaluation Assignment`.`reviewer`={frappe.db.escape(employee)} or (`tabEvaluation Assignment`.`employee`={frappe.db.escape(employee)} and `tabEvaluation Assignment`.`anonymous`=0 and `tabEvaluation Assignment`.`status`='Submitted'))"

def assignment_has_permission(doc,user=None,permission_type=None):
    user=user or frappe.session.user
    if user=="Administrator" or HR.intersection(frappe.get_roles(user)):return None
    employee=frappe.db.get_value("Employee",{"user_id":user},"name")
    if doc.reviewer==employee:
        return True if permission_type in (None,"read","select","write","print","email") and doc.status not in {"Submitted","Replaced","Cancelled"} else permission_type in (None,"read","select","print","email")
    if doc.employee==employee and not doc.anonymous and doc.status=="Submitted":return permission_type in (None,"read","select","print")
    return False
