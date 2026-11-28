from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import add_days, get_datetime, now_datetime

MATCH_FIELDS = (
    "company", "case_type", "category", "stakeholder_type", "project",
    "department", "channel", "severity", "confidentiality", "related_doctype",
)


def _rule_specificity(rule):
    return sum(1 for fieldname in MATCH_FIELDS if rule.get(fieldname))


def _rule_matches(rule, doc):
    return all(not rule.get(fieldname) or rule.get(fieldname) == doc.get(fieldname) for fieldname in MATCH_FIELDS)


def matching_rules(doc):
    rows = frappe.get_all(
        "Accountability Routing Rule",
        filters={"enabled": 1},
        fields=["name", "priority", *MATCH_FIELDS, "receiving_role", "receiving_department",
                "default_responsible_user", "escalation_role", "acknowledgement_days",
                "response_days", "investigation_required", "specialized_referral"],
        order_by="priority asc, modified desc",
    )
    matched = [frappe._dict(row) for row in rows if _rule_matches(row, doc)]
    for row in matched:
        row.specificity = _rule_specificity(row)
    return sorted(matched, key=lambda row: (int(row.priority or 100), -row.specificity, row.name))


def resolve_routing_rule(doc):
    matched = matching_rules(doc)
    if not matched:
        return None
    winner = matched[0]
    conflicts = [row for row in matched[1:] if int(row.priority or 100) == int(winner.priority or 100) and row.specificity == winner.specificity]
    if conflicts:
        frappe.throw(
            _("Ambiguous accountability routing rules with the same priority and specificity: {0}").format(
                ", ".join([winner.name, *[row.name for row in conflicts]])
            )
        )
    return winner


def apply_routing(doc, *, require_match=False):
    rule = resolve_routing_rule(doc)
    if not rule:
        if require_match:
            frappe.throw(_("No active Accountability Routing Rule matches this case."))
        return None
    doc.receiving_role = rule.receiving_role
    doc.receiving_department = rule.receiving_department
    if rule.default_responsible_user:
        _validate_responsible(rule.default_responsible_user, rule.receiving_role)
        doc.custom_current_responsible_user = rule.default_responsible_user
    if rule.investigation_required:
        doc.investigation_required = 1
    if rule.acknowledgement_days is not None:
        doc.acknowledgement_due_on = add_days(doc.received_on or now_datetime(), int(rule.acknowledgement_days or 0))
    if rule.response_days is not None:
        doc.response_due_on = add_days(doc.received_on or now_datetime(), int(rule.response_days or 0))
    doc.flags.qorg_routing_rule = rule.name
    return rule


def _validate_responsible(user, role=None):
    if not frappe.db.exists("User", {"name": user, "enabled": 1}):
        frappe.throw(_("Responsible User must be an enabled user."))
    if role and not frappe.db.exists("Has Role", {"parent": user, "role": role}):
        frappe.throw(_("Responsible User must have the receiving role {0}.").format(role))
