import frappe
from qorg.qorg.employee_lifecycle.training import cancel_assessment, generate_follow_ups, submit_assessment, sync_training_result

@frappe.whitelist()
def submit(name):
    return submit_assessment(name)

@frappe.whitelist()
def cancel(name, reason):
    return cancel_assessment(name, reason)

@frappe.whitelist()
def recalculate(training_event):
    frappe.get_doc("Training Event", training_event).check_permission("read")
    return sync_training_result(training_event)

@frappe.whitelist()
def create_follow_ups(training_event):
    frappe.get_doc("Training Event", training_event).check_permission("write")
    return generate_follow_ups(training_event)
