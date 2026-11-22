
@frappe.whitelist()
def movement_timeline(employee):
    from qorg.qorg.employee_lifecycle.movements import employee_movement_timeline
    frappe.get_doc("Employee", employee).check_permission("read")
    return employee_movement_timeline(employee)
