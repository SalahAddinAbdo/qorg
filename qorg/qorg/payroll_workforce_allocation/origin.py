import frappe

ORIGIN_FIELDS = ("project", "cost_center", "funding_agreement", "budget_line")

def explicit_origin(detail, allowed_destinations):
    reference = detail.get("additional_salary")
    if not reference or not frappe.db.exists("Additional Salary", reference):
        return []
    document = frappe.get_doc("Additional Salary", reference)
    values = {field: document.get(field) for field in ORIGIN_FIELDS if document.meta.has_field(field) and document.get(field)}
    project = values.get("project")
    if not project:
        return []
    allowed = next((row for row in allowed_destinations if row.get("project") == project), None)
    if not allowed:
        return []
    row = frappe._dict(allowed)
    for field, value in values.items():
        row[field] = value
    row.share = 100
    row.evidence_type = "Additional Salary"
    row.evidence_reference = reference
    return [row]
