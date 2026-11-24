import json
import frappe
from qorg.qorg.employee_lifecycle.performance import create_feedback, decline_assignment, generate_assignments, replace_assignment

@frappe.whitelist()
def generate(appraisal, manual_reviewers=None):
    reviewers=json.loads(manual_reviewers) if isinstance(manual_reviewers,str) and manual_reviewers else (manual_reviewers or {})
    return generate_assignments(appraisal,reviewers)

@frappe.whitelist()
def feedback(assignment):
    return create_feedback(assignment)

@frappe.whitelist()
def replace(name, reviewer, reason):
    return replace_assignment(name,reviewer,reason)

@frappe.whitelist()
def decline(name, reason, conflict=0):
    return decline_assignment(name,reason,bool(int(conflict or 0)))

@frappe.whitelist()
def recalculate(appraisal):
    from qorg.qorg.employee_lifecycle.performance import recalculate_appraisal
    return recalculate_appraisal(appraisal, save=True)

@frappe.whitelist()
def transition(appraisal, stage, reason=None):
    from qorg.qorg.employee_lifecycle.performance import transition_appraisal
    return transition_appraisal(appraisal, stage, reason)
