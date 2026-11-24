import frappe

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def reviewers(doctype, txt, searchfield, start, page_len, filters):
    employee_name = filters.get("employee")
    source = filters.get("source")
    department = filters.get("department")
    employee = frappe.qb.DocType("Employee")
    query = (
        frappe.qb.from_(employee)
        .select(employee.name, employee.employee_name)
        .where(
            (employee.status == "Active")
            & (employee.user_id.isnotnull())
            & ((employee.name.like(f"%{txt}%")) | (employee.employee_name.like(f"%{txt}%")))
        )
        .orderby(employee.employee_name)
        .limit(page_len)
        .offset(start)
    )
    if employee_name:
        query = query.where(employee.name != employee_name)
    if source == "Related Department" and department:
        query = query.where(employee.department == department)
    return query.run()
