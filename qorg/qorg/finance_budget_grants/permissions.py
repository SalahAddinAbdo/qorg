from __future__ import annotations
import frappe
PRIVILEGED_ROLES={"System Manager","Accounts Manager","Financial Manager"}
READ_ROLES=PRIVILEGED_ROLES|{"Accounts User","Projects Manager","Projects User","Budget User",}
def _roles(user): return set(frappe.get_roles(user or frappe.session.user))
def _values(user,doctype): return frappe.get_all("User Permission",filters={"user":user,"allow":doctype},pluck="for_value")
def _scope(alias,user):
    conditions=[]; companies=_values(user,"Company"); projects=_values(user,"Project")
    if companies and alias=="Funding Agreement": conditions.append(f"`tab{alias}`.`company` in ({','.join(frappe.db.escape(x) for x in companies)})")
    if projects: conditions.append(f"`tab{alias}`.`project` in ({','.join(frappe.db.escape(x) for x in projects)})")
    return " and ".join(conditions)
def funding_agreement_query(user=None):
    user=user or frappe.session.user
    if "System Manager" in _roles(user): return ""
    if not (_roles(user)&READ_ROLES): return "1=0"
    scope=_scope("Funding Agreement",user)
    return scope or ("" if _roles(user)&PRIVILEGED_ROLES else "1=0")
def funding_agreement_permission(doc,user=None,permission_type=None):
    user=user or frappe.session.user; roles=_roles(user)
    if permission_type in ("write","create","submit","cancel","amend"): return bool(roles&PRIVILEGED_ROLES)
    return bool(roles&READ_ROLES)
def budget_transfer_audit_query(user=None):
    user=user or frappe.session.user
    if "System Manager" in _roles(user): return ""
    if not (_roles(user)&READ_ROLES): return "1=0"
    scope=_scope("Budget Transfer Audit",user)
    return scope or ("" if _roles(user)&PRIVILEGED_ROLES else "1=0")
def budget_transfer_audit_permission(doc,user=None,permission_type=None):
    if permission_type not in (None,"read","print","email","report","export"): return False
    return bool(_roles(user)&READ_ROLES)
