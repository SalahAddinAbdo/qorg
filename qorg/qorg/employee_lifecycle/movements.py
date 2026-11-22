from __future__ import annotations

import json
import frappe
from frappe import _
from frappe.utils import getdate

MOVEMENT_DOCTYPES = ("Employee Promotion", "Employee Transfer")


def validate_employee_movement(doc, method=None):
    employee = doc.get("employee")
    if not employee:
        return
    effective_date = _effective_date(doc)
    if not effective_date:
        frappe.throw(_("Effective Date is required for an employment movement."))
    employee_doc = frappe.get_doc("Employee", employee)
    if employee_doc.date_of_joining and getdate(effective_date) < getdate(employee_doc.date_of_joining):
        frappe.throw(_("Movement Effective Date cannot be before Date of Joining."))
    contract = _current_contract(employee)
    if contract and contract.end_date and getdate(effective_date) > getdate(contract.end_date):
        frappe.throw(_("Movement Effective Date cannot be after the current Contract End Date."))
    changed = _changed_properties(doc)
    if not changed:
        frappe.throw(_("At least one employee property change is required."))
    _prevent_same_day_conflict(doc, employee, effective_date, changed)
    _validate_impact_links(doc)
    if doc.meta.has_field("qorg_previous_values"):
        doc.qorg_previous_values = json.dumps({field: employee_doc.get(field) for field in changed}, ensure_ascii=False, default=str)
    if doc.meta.has_field("qorg_new_values"):
        doc.qorg_new_values = json.dumps(changed, ensure_ascii=False, default=str)


def movement_submitted(doc, method=None):
    _record_movement_summary(doc, "Submitted")


def before_cancel_employee_movement(doc, method=None):
    employee = doc.get("employee")
    date = _effective_date(doc)
    if not employee or not date:
        return
    changed = set(_changed_properties(doc))
    for dt in MOVEMENT_DOCTYPES:
        if not frappe.db.exists("DocType", dt):
            continue
        for row in frappe.get_all(dt, filters={"employee": employee, "docstatus": 1, "name": ["!=", doc.name]}, fields=["name", "*"], order_by="modified desc"):
            other = frappe.get_doc(dt, row.name)
            other_date = _effective_date(other)
            if other_date and getdate(other_date) > getdate(date) and changed.intersection(_changed_properties(other)):
                frappe.throw(_("Cannot cancel this movement because later movement {0} affects the same employee properties.").format(other.name))


def movement_cancelled(doc, method=None):
    _record_movement_summary(doc, "Cancelled")


def validate_salary_assignment(doc, method=None):
    employee = doc.get("employee")
    effective = doc.get("from_date") or doc.get("effective_from") or doc.get("start_date")
    if not employee or not effective:
        return
    _validate_service_period(employee, effective, _("Salary Structure Assignment"))
    filters = {"employee": employee, "docstatus": 1, "name": ["!=", doc.name or ""]}
    date_field = _first_meta_field(doc.meta, "from_date", "effective_from", "start_date")
    if date_field:
        filters[date_field] = effective
        duplicate = frappe.db.get_value(doc.doctype, filters, "name")
        if duplicate:
            frappe.throw(_("Another submitted Salary Structure Assignment exists on the same effective date: {0}").format(duplicate))


def validate_funding_plan_movement(doc, method=None):
    employee = doc.get("employee")
    effective = doc.get("effective_from")
    if not employee or not effective:
        return
    _validate_service_period(employee, effective, _("Workforce Funding Plan"))
    if doc.get("supersedes_plan"):
        previous = frappe.get_doc("Workforce Funding Plan", doc.supersedes_plan)
        if previous.employee != employee:
            frappe.throw(_("Superseded Workforce Funding Plan must belong to the same Employee."))
        if previous.effective_from and getdate(effective) <= getdate(previous.effective_from):
            frappe.throw(_("The superseding plan must start after the previous plan."))


def validate_contract_amendment_movement(doc, method=None):
    if not doc.get("contract") or not doc.get("effective_date"):
        return
    contract = frappe.get_doc("Contract", doc.contract)
    employee = contract.get("qorg_employee")
    if employee:
        _validate_service_period(employee, doc.effective_date, _("Contract Amendment"), contract)
    duplicate = frappe.db.get_value("Contract Amendment", {"contract": doc.contract, "effective_date": doc.effective_date, "docstatus": ["<", 2], "name": ["!=", doc.name or ""]}, "name")
    if duplicate:
        frappe.throw(_("Another Contract Amendment exists for this contract on the same effective date: {0}").format(duplicate))


def employee_movement_timeline(employee):
    rows = []
    for dt in MOVEMENT_DOCTYPES + ("Salary Structure Assignment", "Workforce Funding Plan"):
        if not frappe.db.exists("DocType", dt):
            continue
        meta = frappe.get_meta(dt)
        if not meta.has_field("employee"):
            continue
        for name in frappe.get_all(dt, filters={"employee": employee, "docstatus": ["<", 2]}, pluck="name"):
            doc = frappe.get_doc(dt, name)
            rows.append({"doctype": dt, "name": name, "effective_date": str(_effective_date(doc) or ""), "docstatus": doc.docstatus, "reason": doc.get("qorg_movement_reason") or doc.get("reason"), "payroll_impact": doc.get("qorg_payroll_impact"), "funding_impact": doc.get("qorg_funding_impact"), "contract_impact": doc.get("qorg_contract_impact")})
    if frappe.db.exists("DocType", "Contract"):
        contracts = frappe.get_all("Contract", filters={"qorg_employee": employee}, pluck="name")
        for contract in contracts:
            for name in frappe.get_all("Contract Amendment", filters={"contract": contract, "docstatus": ["<", 2]}, pluck="name"):
                doc = frappe.get_doc("Contract Amendment", name)
                rows.append({"doctype": "Contract Amendment", "name": name, "effective_date": str(doc.effective_date or ""), "docstatus": doc.docstatus, "reason": doc.reason, "contract_impact": 1})
    return sorted(rows, key=lambda row: (row["effective_date"], row["doctype"], row["name"]), reverse=True)


def _effective_date(doc):
    for fieldname in ("promotion_date", "transfer_date", "effective_date", "from_date", "effective_from", "start_date"):
        if doc.meta.has_field(fieldname) and doc.get(fieldname):
            return doc.get(fieldname)
    return None


def _changed_properties(doc):
    changed = {}
    for table_field in ("promotion_details", "transfer_details", "property_update", "employee_property_update"):
        if not doc.meta.has_field(table_field):
            continue
        for row in doc.get(table_field) or []:
            fieldname = row.get("property") or row.get("fieldname")
            value = row.get("new") if row.get("new") is not None else row.get("new_value")
            if fieldname:
                changed[fieldname] = value
    for fieldname in ("designation", "department", "branch", "reports_to", "grade", "employment_type", "company", "cost_center"):
        if doc.meta.has_field(fieldname) and doc.get(fieldname) not in (None, ""):
            changed[fieldname] = doc.get(fieldname)
    return changed


def _prevent_same_day_conflict(doc, employee, effective_date, changed):
    changed_fields = set(changed)
    for dt in MOVEMENT_DOCTYPES:
        if not frappe.db.exists("DocType", dt):
            continue
        for name in frappe.get_all(dt, filters={"employee": employee, "docstatus": ["<", 2], "name": ["!=", doc.name or ""]}, pluck="name"):
            other = frappe.get_doc(dt, name)
            if _effective_date(other) and getdate(_effective_date(other)) == getdate(effective_date) and changed_fields.intersection(_changed_properties(other)):
                frappe.throw(_("Movement {0} changes the same employee property on the same effective date.").format(name))


def _validate_impact_links(doc):
    checks = (("qorg_payroll_impact", "qorg_salary_structure_assignment", "Salary Structure Assignment"), ("qorg_funding_impact", "qorg_workforce_funding_plan", "Workforce Funding Plan"), ("qorg_contract_impact", "qorg_contract_amendment", "Contract Amendment"))
    for flag, link, label in checks:
        if doc.meta.has_field(flag) and doc.get(flag) and (not doc.meta.has_field(link) or not doc.get(link)):
            frappe.throw(_("{0} is required when {1} is selected.").format(label, doc.meta.get_label(flag)))


def _validate_service_period(employee, effective_date, label, contract=None):
    employee_doc = frappe.get_doc("Employee", employee)
    if employee_doc.date_of_joining and getdate(effective_date) < getdate(employee_doc.date_of_joining):
        frappe.throw(_("{0} date cannot be before Date of Joining.").format(label))
    contract = contract or _current_contract(employee)
    if contract and contract.end_date and getdate(effective_date) > getdate(contract.end_date):
        frappe.throw(_("{0} date cannot be after Contract End Date.").format(label))


def _current_contract(employee):
    name = frappe.db.get_value("Contract", {"qorg_employee": employee, "qorg_contract_type": "Employment Contract", "docstatus": ["<", 2]}, "name", order_by="start_date desc") if frappe.db.exists("DocType", "Contract") else None
    return frappe.get_doc("Contract", name) if name else None


def _first_meta_field(meta, *names):
    return next((name for name in names if meta.has_field(name)), None)


def _record_movement_summary(doc, state):
    employee = doc.get("employee")
    if not employee:
        return
    message = _("{0} {1} on {2}. Reason: {3}").format(doc.doctype, state, _effective_date(doc) or "", doc.get("qorg_movement_reason") or doc.get("reason") or "")
    frappe.get_doc({"doctype": "Comment", "comment_type": "Info", "reference_doctype": "Employee", "reference_name": employee, "content": message}).insert(ignore_permissions=True)
