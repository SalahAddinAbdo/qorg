import frappe
def behavior_code(opportunity_type: str | None) -> str | None:
    return frappe.db.get_value("External Opportunity Type",opportunity_type,"behavior_code") if opportunity_type else None
def require_behavior(opportunity_type: str, expected: str):
    actual=behavior_code(opportunity_type)
    if actual!=expected:frappe.throw(f"Opportunity Type must have behavior {expected}.")
