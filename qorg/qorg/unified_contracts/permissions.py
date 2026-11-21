from __future__ import annotations

import frappe

PRIVILEGED = {"System Manager", "HR Manager", "Procurement Manager", "Accounts Manager", "Auditor"}


def contract_query_condition(user=None):
    user = user or frappe.session.user
    if user == "Administrator" or PRIVILEGED.intersection(frappe.get_roles(user)):
        return ""
    esc = frappe.db.escape(user)
    employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
    employee_clause = f" OR (`tabContract`.`party_type`='Employee' AND `tabContract`.`party_name`={frappe.db.escape(employee)})" if employee else ""
    return f"(`tabContract`.`qorg_confidential`=0 OR `tabContract`.`qorg_contract_manager`={esc} OR `tabContract`.`qorg_legal_owner`={esc}{employee_clause})"


def contract_has_permission(doc, user=None, permission_type=None):
    user = user or frappe.session.user
    if user == "Administrator" or PRIVILEGED.intersection(frappe.get_roles(user)):
        return None
    if not doc.get("qorg_confidential"):
        return None
    if user in {doc.get("qorg_contract_manager"), doc.get("qorg_legal_owner"), doc.get("party_user")}:
        return True
    employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
    if doc.get("party_type") == "Employee" and doc.get("party_name") == employee:
        return permission_type in {None, "read", "select", "print", "email"}
    return False
