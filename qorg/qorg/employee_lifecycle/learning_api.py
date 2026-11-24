import json
import frappe
from qorg.qorg.employee_lifecycle.learning import convert_training_need, resolve_participants, transition_training_need

@frappe.whitelist()
def transition(name, action, reason=None):
    return transition_training_need(name, action, reason)

@frappe.whitelist()
def preview_participants(name):
    doc = frappe.get_doc("Training Need Request", name)
    doc.check_permission("read")
    employees = resolve_participants(doc)
    return {"count": len(employees), "employees": employees[:200], "truncated": len(employees) > 200}

@frappe.whitelist()
def convert(name, mode, existing_program=None, event_values=None):
    values = json.loads(event_values) if isinstance(event_values, str) and event_values else (event_values or {})
    return convert_training_need(name, mode, existing_program, values)
