from __future__ import annotations

import frappe

PRIVILEGED = {"System Manager", "Accountability Manager", "Compliance Manager"}
CONFIG = {
    "Enterprise Risk": "risk_owner",
    "Compliance Obligation": "responsible_user",
    "Assurance Finding": "responsible_user",
    "Corrective Action": "responsible_user",
}


def _company_condition(doctype, user):
    companies = frappe.get_all(
        "User Permission",
        filters={"user": user, "allow": "Company", "applicable_for": ["in", [None, "", doctype]]},
        pluck="for_value",
        limit_page_length=0,
    )
    if not companies:
        return ""
    values = ", ".join(frappe.db.escape(value) for value in companies)
    return f" and `tab{doctype}`.`company` in ({values})"


def query(doctype, user=None):
    user = user or frappe.session.user
    if user == "Administrator" or PRIVILEGED.intersection(frappe.get_roles(user)):
        return ""
    field = CONFIG[doctype]
    escaped = frappe.db.escape(user)
    return f"(`tab{doctype}`.`owner`={escaped} or `tab{doctype}`.`{field}`={escaped})" + _company_condition(doctype, user)


def has_permission(doc, user=None, permission_type=None):
    user = user or frappe.session.user
    if user == "Administrator" or PRIVILEGED.intersection(frappe.get_roles(user)):
        return True
    if user not in {doc.owner, doc.get(CONFIG[doc.doctype])}:
        return False
    companies = frappe.get_all(
        "User Permission",
        filters={"user": user, "allow": "Company", "applicable_for": ["in", [None, "", doc.doctype]]},
        pluck="for_value",
        limit_page_length=0,
    )
    return not companies or not doc.company or doc.company in companies


def enterprise_risk_query(user=None): return query("Enterprise Risk", user)
def compliance_obligation_query(user=None): return query("Compliance Obligation", user)
def assurance_finding_query(user=None): return query("Assurance Finding", user)
def corrective_action_query(user=None): return query("Corrective Action", user)
