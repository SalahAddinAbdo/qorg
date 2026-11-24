import json
import frappe
from qorg.qorg.employee_lifecycle.development import create_appraisal_recommendation, create_gap_actions, skill_gaps
from qorg.qorg.employee_lifecycle.history import employee_history

@frappe.whitelist()
def gaps(employee):
    frappe.get_doc("Employee", employee).check_permission("read")
    return skill_gaps(employee)

@frappe.whitelist()
def gap_actions(employee, responsible_user, target_date, skills=None):
    selected=json.loads(skills) if isinstance(skills,str) and skills else (skills or [])
    return create_gap_actions(employee,responsible_user,target_date,selected)

@frappe.whitelist()
def recommendation(appraisal, recommendation_type, values=None):
    parsed=json.loads(values) if isinstance(values,str) and values else (values or {})
    return create_appraisal_recommendation(appraisal,recommendation_type,parsed)

@frappe.whitelist()
def history(employee):
    return employee_history(employee)
