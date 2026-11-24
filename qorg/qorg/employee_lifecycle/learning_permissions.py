import frappe

HR_ROLES = {"HR Manager", "HR User", "System Manager"}

def training_need_query(user=None):
    user = user or frappe.session.user
    if user == "Administrator" or HR_ROLES.intersection(frappe.get_roles(user)):
        return ""
    employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
    parts = [f"`tabTraining Need Request`.`requested_by`={frappe.db.escape(user)}"]
    if employee:
        parts.append(f"`tabTraining Need Request`.`requested_for_employee`={frappe.db.escape(employee)}")
        parts.append(f"exists (select 1 from `tabTraining Need Participant` p where p.parent=`tabTraining Need Request`.name and p.employee={frappe.db.escape(employee)} and p.include=1)")
    return "(" + " or ".join(parts) + ")"

def training_need_has_permission(doc, user=None, permission_type=None):
    user = user or frappe.session.user
    if user == "Administrator" or HR_ROLES.intersection(frappe.get_roles(user)):
        return None
    employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
    own = doc.requested_by == user or (employee and doc.requested_for_employee == employee) or any(row.employee == employee and row.include for row in doc.participants)
    if not own:
        return False
    if permission_type in (None, "read", "select", "print", "email"):
        return True
    return doc.status in {"Draft", "Returned"} and doc.requested_by == user

def development_action_query(user=None):
    user = user or frappe.session.user
    if user == "Administrator" or HR_ROLES.intersection(frappe.get_roles(user)):
        return ""
    employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
    conditions = [f"`tabDevelopment Action`.`responsible_person`={frappe.db.escape(user)}"]
    if employee:
        conditions.append(f"`tabDevelopment Action`.`employee`={frappe.db.escape(employee)}")
    return "(" + " or ".join(conditions) + ")"

def development_action_has_permission(doc, user=None, permission_type=None):
    user = user or frappe.session.user
    if user == "Administrator" or HR_ROLES.intersection(frappe.get_roles(user)):
        return None
    employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
    if doc.employee != employee and doc.responsible_person != user:
        return False
    return permission_type in (None, "read", "select", "print", "email") or (doc.responsible_person == user and doc.status not in {"Completed", "Cancelled"})
