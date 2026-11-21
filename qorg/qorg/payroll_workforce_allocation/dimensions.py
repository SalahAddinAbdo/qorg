import json
import frappe
from frappe import _

def active_dimensions():
    if not frappe.db.exists("DocType", "Accounting Dimension"):
        return []
    meta = frappe.get_meta("Accounting Dimension")
    fields = ["name", "fieldname", "document_type"]
    if meta.has_field("disabled"):
        filters = {"disabled": 0}
    else:
        filters = {}
    return [frappe._dict(row) for row in frappe.get_all("Accounting Dimension", filters=filters, fields=fields, order_by="idx asc", limit_page_length=0)]

def _dimension_default(document_type, reference_name, fieldname):
    if not document_type or not reference_name or not frappe.db.exists("DocType", document_type):
        return None
    meta = frappe.get_meta(document_type)
    return frappe.db.get_value(document_type, reference_name, fieldname) if meta.has_field(fieldname) else None

def resolve_dimensions(destination, company=None, account=None, employee=None):
    values = {"project": destination.get("project"), "cost_center": destination.get("cost_center")}
    for dim in active_dimensions():
        fieldname = dim.fieldname
        if values.get(fieldname):
            continue
        explicit = destination.get(fieldname)
        if explicit:
            values[fieldname] = explicit
            continue
        if fieldname == "budget_line" and destination.get("budget_line"):
            values[fieldname] = destination.get("budget_line")
        elif fieldname == "funding_agreement" and destination.get("funding_agreement"):
            values[fieldname] = destination.get("funding_agreement")
        else:
            values[fieldname] = _dimension_default("Project", destination.get("project"), fieldname) or _dimension_default("Employee", employee, fieldname) or _dimension_default("Company", company, fieldname)
    return {key: value for key, value in values.items() if value}

def validate_dimensions(dimensions, company, account=None):
    issues = []
    row_meta = frappe.get_meta("Journal Entry Account")
    for key, value in dimensions.items():
        field = row_meta.get_field(key)
        if not field:
            continue
        if field.fieldtype == "Link" and field.options and not frappe.db.exists(field.options, value):
            issues.append(_("Invalid {0}: {1}").format(field.label, value))
    if dimensions.get("project"):
        project_company = frappe.db.get_value("Project", dimensions.get("project"), "company")
        if project_company and project_company != company:
            issues.append(_("Project belongs to another company."))
    if dimensions.get("cost_center"):
        cc_company = frappe.db.get_value("Cost Center", dimensions.get("cost_center"), "company")
        if cc_company and cc_company != company:
            issues.append(_("Cost Center belongs to another company."))
    return issues

def apply_dimensions(row, dimensions):
    meta = frappe.get_meta("Journal Entry Account")
    for key, value in dimensions.items():
        if meta.has_field(key):
            row.set(key, value)

def snapshot(dimensions):
    return json.dumps(dimensions, sort_keys=True, default=str)
