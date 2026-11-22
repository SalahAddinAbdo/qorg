from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field

import frappe
from frappe import _
from frappe.utils import getdate, now_datetime, today


@dataclass
class ServiceCheck:
    service: str
    ready: bool
    effective_date: str | None = None
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    evidence: dict = field(default_factory=dict)


@dataclass
class ReadinessResult:
    employee: str
    evaluated_on: str
    services: dict[str, ServiceCheck]

    @property
    def overall_status(self):
        ready = [row.ready for row in self.services.values()]
        if all(ready):
            return "Ready"
        if any(ready):
            return "Partially Ready"
        return "Blocked"

    def as_dict(self):
        return {
            "employee": self.employee,
            "evaluated_on": self.evaluated_on,
            "overall_status": self.overall_status,
            "services": {name: asdict(row) for name, row in self.services.items()},
        }


def evaluate_employee_readiness(employee_name, persist=True):
    employee = frappe.get_doc("Employee", employee_name)
    contract = _employment_contract(employee)
    template = _contract_template(contract)
    employment = _employment_check(employee, contract, template)
    payroll = _payroll_check(employee, contract, template, employment)
    attendance = _attendance_check(employee, contract, template, employment)
    leave = _leave_check(employee, contract, template, employment)
    result = ReadinessResult(employee.name, str(now_datetime()), {
        "employment": employment,
        "payroll": payroll,
        "attendance": attendance,
        "leave": leave,
    })
    if persist:
        _persist_readiness(employee, result)
    return result


def activate_ready_services(employee_name, services=None, effective_dates=None):
    employee = frappe.get_doc("Employee", employee_name)
    employee.check_permission("write")
    result = evaluate_employee_readiness(employee_name, persist=False)
    requested = services or list(result.services)
    invalid = sorted(set(requested) - set(result.services))
    if invalid:
        frappe.throw(_("Unknown services: {0}").format(", ".join(invalid)))
    effective_dates = effective_dates or {}
    activated = []
    blockers = {}
    field_map = {
        "employment": "qorg_employment_effective_date",
        "payroll": "qorg_payroll_effective_date",
        "attendance": "qorg_attendance_effective_date",
        "leave": "qorg_leave_effective_date",
    }
    values = {}
    for service in requested:
        check = result.services[service]
        if not check.ready:
            blockers[service] = check.blockers
            continue
        fieldname = field_map[service]
        proposed = effective_dates.get(service) or check.effective_date or employee.date_of_joining or today()
        _validate_activation_date(employee, contract=_employment_contract(employee), service=service, value=proposed)
        if employee.meta.has_field(fieldname) and not employee.get(fieldname):
            values[fieldname] = proposed
            activated.append(service)
    if blockers:
        frappe.throw(_("Services are blocked: {0}").format(json.dumps(blockers, ensure_ascii=False)))
    if values:
        values["qorg_service_activation_status"] = "Activated" if set(requested) == set(result.services) else "Partially Ready"
        values["qorg_service_activated_on"] = now_datetime()
        values["qorg_service_activated_by"] = frappe.session.user
        frappe.db.set_value("Employee", employee.name, values, update_modified=True)
    evaluate_employee_readiness(employee.name, persist=True)
    return {"employee": employee.name, "activated": activated, "effective_dates": values}


def _employment_check(employee, contract, template):
    blockers, warnings, evidence = [], [], {}
    if employee.status != "Active":
        blockers.append(_("Employee must be Active."))
    if not employee.date_of_joining:
        blockers.append(_("Date of Joining is required."))
    if not contract:
        blockers.append(_("An Employment Contract is required."))
    else:
        evidence["contract"] = contract.name
        if contract.docstatus == 2 or contract.get("qorg_lifecycle_status") in {"Cancelled", "Terminated", "Expired", "Superseded"}:
            blockers.append(_("Employment Contract is not current."))
        if contract.get("qorg_lifecycle_status") not in {"Active", "Approved"}:
            blockers.append(_("Employment Contract must be Approved or Active."))
        if template and template.get("qorg_changes_require_legal_review") and contract.get("qorg_terms_modified_after_copy"):
            blockers.append(_("Modified contract terms require legal review."))
        if contract.meta.has_field("is_signed") and not contract.get("is_signed"):
            blockers.append(_("Employment Contract must be signed."))
        if template and template.get("qorg_work_commencement_required") and not contract.get("qorg_work_commencement_notice"):
            blockers.append(_("Work Commencement Notice is required by the Contract Template."))
        if template and template.get("qorg_onboarding_required"):
            onboarding = _onboarding(employee.name)
            if not onboarding:
                blockers.append(_("Employee Onboarding is required."))
            else:
                evidence["onboarding"] = onboarding.name
                completion = onboarding.get("qorg_completion_percent")
                if completion is not None and float(completion or 0) < 100:
                    blockers.append(_("Employee Onboarding must reach 100% completion."))
                elif onboarding.docstatus == 0 and completion is None:
                    blockers.append(_("Employee Onboarding must be submitted or completed."))
    return ServiceCheck("employment", not blockers, _date(employee, contract, "employment"), blockers, warnings, evidence)


def _payroll_check(employee, contract, template, employment):
    blockers = list(employment.blockers)
    evidence = dict(employment.evidence)
    if template and template.get("qorg_bank_details_required") and not _first_employee_value(employee, "bank_ac_no", "bank_account", "salary_bank_account"):
        blockers.append(_("Bank details are required for payroll."))
    if template is None or template.get("qorg_salary_assignment_required", 1):
        assignment = _effective_assignment("Salary Structure Assignment", employee.name, _date(employee, contract, "payroll"))
        if not assignment:
            blockers.append(_("A submitted Salary Structure Assignment effective on or before payroll activation is required."))
        else:
            evidence["salary_structure_assignment"] = assignment
    cost_center = _first_employee_value(employee, "payroll_cost_center", "cost_center")
    if not cost_center:
        blockers.append(_("Payroll Cost Center is required."))
    else:
        evidence["cost_center"] = cost_center
    blockers.extend(_accounting_dimension_blockers(employee))
    return ServiceCheck("payroll", not blockers, _date(employee, contract, "payroll"), blockers, [], evidence)


def _attendance_check(employee, contract, template, employment):
    blockers = list(employment.blockers)
    evidence = dict(employment.evidence)
    holiday_required = True if template is None else bool(template.get("qorg_holiday_list_required", 1))
    if holiday_required and not _first_employee_value(employee, "holiday_list", "default_holiday_list"):
        blockers.append(_("Holiday List is required for attendance."))
    shift_required = bool(template and template.get("qorg_shift_assignment_required"))
    if shift_required:
        assignment = _effective_assignment("Shift Assignment", employee.name, _date(employee, contract, "attendance"))
        if not assignment:
            blockers.append(_("A current Shift Assignment is required."))
        else:
            evidence["shift_assignment"] = assignment
    return ServiceCheck("attendance", not blockers, _date(employee, contract, "attendance"), blockers, [], evidence)


def _leave_check(employee, contract, template, employment):
    blockers = list(employment.blockers)
    evidence = dict(employment.evidence)
    leave_required = True if template is None else bool(template.get("qorg_leave_policy_required", 1))
    if leave_required:
        assignment = _effective_assignment("Leave Policy Assignment", employee.name, _date(employee, contract, "leave"))
        if not assignment:
            blockers.append(_("A submitted Leave Policy Assignment effective on or before leave activation is required."))
        else:
            evidence["leave_policy_assignment"] = assignment
    return ServiceCheck("leave", not blockers, _date(employee, contract, "leave"), blockers, [], evidence)


def _employment_contract(employee):
    if employee.get("qorg_employment_contract") and frappe.db.exists("Contract", employee.qorg_employment_contract):
        return frappe.get_doc("Contract", employee.qorg_employment_contract)
    name = frappe.db.get_value("Contract", {"qorg_employee": employee.name, "qorg_contract_type": "Employment Contract", "docstatus": ["<", 2]}, "name", order_by="start_date desc")
    return frappe.get_doc("Contract", name) if name else None


def _contract_template(contract):
    return frappe.get_doc("Contract Template", contract.contract_template) if contract and contract.contract_template and frappe.db.exists("Contract Template", contract.contract_template) else None


def _onboarding(employee_name):
    name = frappe.db.get_value("Employee Onboarding", {"employee": employee_name, "docstatus": ["<", 2]}, "name", order_by="modified desc")
    return frappe.get_doc("Employee Onboarding", name) if name else None


def _effective_assignment(doctype, employee_name, effective_date):
    if not frappe.db.exists("DocType", doctype):
        return None
    meta = frappe.get_meta(doctype)
    filters = {"employee": employee_name, "docstatus": 1}
    date_field = next((f for f in ("from_date", "effective_from", "start_date") if meta.has_field(f)), None)
    if date_field and effective_date:
        filters[date_field] = ["<=", effective_date]
    return frappe.db.get_value(doctype, filters, "name", order_by=f"{date_field} desc" if date_field else "modified desc")


def _date(employee, contract, service):
    fields = {
        "employment": "qorg_employment_effective_date",
        "payroll": "qorg_payroll_effective_date",
        "attendance": "qorg_attendance_effective_date",
        "leave": "qorg_leave_effective_date",
    }
    employee_value = employee.get(fields[service]) if employee.meta.has_field(fields[service]) else None
    contract_value = contract.get(fields[service]) if contract and contract.meta.has_field(fields[service]) else None
    return str(employee_value or contract_value or employee.date_of_joining or today())


def _first_employee_value(employee, *fields):
    for fieldname in fields:
        if employee.meta.has_field(fieldname) and employee.get(fieldname):
            return employee.get(fieldname)
    return None


def _accounting_dimension_blockers(employee):
    if not frappe.db.exists("DocType", "Accounting Dimension"):
        return []
    meta = frappe.get_meta("Accounting Dimension")
    fields = ["name"]
    for fieldname in ("fieldname", "disabled", "mandatory_for_pl", "mandatory_for_bs"):
        if meta.has_field(fieldname):
            fields.append(fieldname)
    blockers = []
    for row in frappe.get_all("Accounting Dimension", fields=fields):
        if row.get("disabled"):
            continue
        if not (row.get("mandatory_for_pl") or row.get("mandatory_for_bs")):
            continue
        fieldname = row.get("fieldname")
        if fieldname and employee.meta.has_field(fieldname) and not employee.get(fieldname):
            blockers.append(_("Accounting Dimension {0} is required.").format(row.name))
    return blockers


def _validate_activation_date(employee, contract, service, value):
    value = getdate(value)
    if employee.date_of_joining and value < getdate(employee.date_of_joining):
        frappe.throw(_("{0} activation cannot be before Date of Joining.").format(service.title()))
    if contract and contract.end_date and value > getdate(contract.end_date):
        frappe.throw(_("{0} activation cannot be after Contract End Date.").format(service.title()))


def _persist_readiness(employee, result):
    data = result.as_dict()
    blockers = []
    for service, check in data["services"].items():
        blockers.extend([f"{service}: {item}" for item in check["blockers"]])
    values = {}
    activated_fields = ["qorg_employment_effective_date", "qorg_payroll_effective_date", "qorg_attendance_effective_date", "qorg_leave_effective_date"]
    all_activated = all(employee.get(fieldname) for fieldname in activated_fields if employee.meta.has_field(fieldname))
    persisted_status = "Activated" if all_activated else data["overall_status"]
    mapping = {
        "qorg_service_activation_status": persisted_status,
        "qorg_service_readiness_json": json.dumps(data, ensure_ascii=False, default=str),
        "qorg_service_blockers": "\n".join(blockers),
        "qorg_service_last_evaluated_on": now_datetime(),
    }
    for fieldname, value in mapping.items():
        if employee.meta.has_field(fieldname):
            values[fieldname] = value
    if values:
        frappe.db.set_value("Employee", employee.name, values, update_modified=False)
