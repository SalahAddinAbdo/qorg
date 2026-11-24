import frappe

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def event_employees(doctype, txt, searchfield, start, page_len, filters):
    event = filters.get("training_event")
    if not event:
        return []
    table = frappe.qb.DocType("Training Event Employee")
    employee = frappe.qb.DocType("Employee")
    return (
        frappe.qb.from_(table)
        .join(employee).on(employee.name == table.employee)
        .select(employee.name, employee.employee_name)
        .where((table.parent == event) & (employee.status == "Active") & ((employee.name.like(f"%{txt}%")) | (employee.employee_name.like(f"%{txt}%"))))
        .orderby(employee.employee_name)
        .limit(page_len)
        .offset(start)
    ).run()
