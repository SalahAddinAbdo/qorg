from __future__ import annotations
import frappe
MANAGER_ROLES={"System Manager","Accountability Manager"};SENSITIVE_LEVELS={"Confidential","Highly Confidential"}
def _companies(user,doctype):return frappe.get_all("User Permission",filters={"user":user,"allow":"Company","applicable_for":["in",[None,"",doctype]]},pluck="for_value",limit_page_length=0)
def _company_sql(user,doctype):
    cs=_companies(user,doctype)
    return "" if not cs else " and `tab%s`.`company` in (%s)"%(doctype,", ".join(frappe.db.escape(x) for x in cs))
def accountability_case_query(user=None):
    user=user or frappe.session.user
    if user=="Administrator" or MANAGER_ROLES.intersection(frappe.get_roles(user)):return ""
    roles=", ".join(frappe.db.escape(x) for x in frappe.get_roles(user)) or "''";u=frappe.db.escape(user)
    base="(`tabAccountability Case`.`owner`={u} or `tabAccountability Case`.`custom_current_responsible_user`={u} or (`tabAccountability Case`.`receiving_role` in ({roles}) and `tabAccountability Case`.`confidentiality` in ('Standard','Restricted')))".format(u=u,roles=roles)
    return base+_company_sql(user,"Accountability Case")
def accountability_case_permission(doc,user=None,permission_type=None):
    user=user or frappe.session.user
    if user=="Administrator" or MANAGER_ROLES.intersection(frappe.get_roles(user)):return True
    cs=_companies(user,"Accountability Case")
    if cs and doc.company and doc.company not in cs:return False
    if doc.owner==user or doc.custom_current_responsible_user==user:return True
    if doc.confidentiality in SENSITIVE_LEVELS:return False
    return bool(doc.receiving_role and doc.receiving_role in frappe.get_roles(user))
