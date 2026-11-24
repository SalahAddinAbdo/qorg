from __future__ import annotations

import frappe


def employee_history(employee):
    """Read-only projection over authoritative lifecycle sources; no duplicated history table."""
    frappe.get_doc("Employee", employee).check_permission("read")
    rows = []
    _append(rows, "Training Need Request", {"requested_for_employee": employee}, "request_date", "training_need_title", "status")
    if frappe.db.exists("DocType", "Training Need Participant"):
        request_names = frappe.get_all("Training Need Participant", filters={"employee": employee, "include": 1}, pluck="parent")
        for request_name in sorted(set(request_names)):
            _append(rows, "Training Need Request", {"name": request_name}, "request_date", "training_need_title", "status")
    if frappe.db.exists("DocType", "Training Event Employee"):
        event_names = frappe.get_all("Training Event Employee", filters={"employee": employee}, pluck="parent")
        for event_name in sorted(set(event_names)):
            _append(rows, "Training Event", {"name": event_name}, "end_time", "event_name", "event_status")
    if frappe.db.exists("DocType", "Training Result Employee"):
        result_names = frappe.get_all("Training Result Employee", filters={"employee": employee}, pluck="parent")
        for result_name in sorted(set(result_names)):
            _append(rows, "Training Result", {"name": result_name}, "modified", "training_event", "docstatus")
    _append(rows, "Development Action", {"employee": employee}, "target_date", "development_need", "status")
    _append(rows, "Training Assessment", {"employee": employee}, "assessment_date", "assessment_type", "status")
    _append(rows, "Training Follow-up", {"employee": employee}, "due_date", "training_event", "status")
    _append(rows, "Appraisal", {"employee": employee}, "end_date", "appraisal_cycle", "qorg_stage")
    _append(rows, "Evaluation Assignment", {"employee": employee}, "due_date", "evaluation_source", "status", anonymous=True)
    _append(rows, "Employee Promotion", {"employee": employee}, _date_field("Employee Promotion", "promotion_date", "effective_date"), "name", "docstatus")
    _append(rows, "Employee Transfer", {"employee": employee}, _date_field("Employee Transfer", "transfer_date", "effective_date"), "name", "docstatus")
    _append(rows, "Salary Structure Assignment", {"employee": employee}, _date_field("Salary Structure Assignment", "from_date", "effective_from"), "salary_structure", "docstatus")
    _append(rows, "Workforce Funding Plan", {"employee": employee}, "effective_from", "name", "status")
    contracts = frappe.get_all("Contract", filters={"qorg_employee": employee}, pluck="name") if frappe.db.exists("DocType", "Contract") else []
    for contract in contracts:
        _append(rows, "Contract Amendment", {"contract": contract}, "effective_date", "reason", "docstatus")
    _append(rows, "Employee Document Record", {"subject_doctype": "Employee", "subject_name": employee}, "expiry_date", "document_type", "status")
    unique = {(row["doctype"], row["name"]): row for row in rows}
    return sorted(unique.values(), key=lambda row: (row.get("date") or "", row["doctype"], row["name"]), reverse=True)


def _append(target, doctype, filters, date_field, summary_field, status_field, anonymous=False):
    if not frappe.db.exists("DocType", doctype):
        return
    meta = frappe.get_meta(doctype)
    fields = ["name"]
    for fieldname in {date_field, summary_field, status_field, "anonymous"}:
        if fieldname and meta.has_field(fieldname):
            fields.append(fieldname)
    for row in frappe.get_all(doctype, filters=filters, fields=fields):
        if anonymous and row.get("anonymous") and "HR Manager" not in frappe.get_roles() and "HR User" not in frappe.get_roles():
            continue
        status = row.get(status_field)
        if status_field == "docstatus":
            status = {0: "Draft", 1: "Submitted", 2: "Cancelled"}.get(status, status)
        target.append({"doctype": doctype, "name": row.name, "date": str(row.get(date_field) or ""), "summary": str(row.get(summary_field) or row.name), "status": str(status or "")})


def _date_field(doctype, *candidates):
    meta = frappe.get_meta(doctype) if frappe.db.exists("DocType", doctype) else None
    return next((field for field in candidates if meta and meta.has_field(field)), candidates[0])
