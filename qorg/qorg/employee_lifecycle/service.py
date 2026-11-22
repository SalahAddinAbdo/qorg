from __future__ import annotations

from dataclasses import dataclass, field

import frappe
from frappe import _
from frappe.utils import add_months, cint, getdate


@dataclass
class CommencementResult:
    employee: str
    contract: str | None = None
    onboarding: str | None = None
    created: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def as_dict(self):
        return {
            "employee": self.employee,
            "contract": self.contract,
            "onboarding": self.onboarding,
            "created": self.created,
            "warnings": self.warnings,
        }


def prepare_commencement(doc, method=None):
    """Idempotently prepare Employee, Employment Contract and Onboarding before submit."""
    _validate_commencement_gate(doc)
    employee, employee_created = create_or_link_employee_from_commencement(doc)
    doc.employee = employee
    contract, contract_created = create_or_link_employment_contract(doc, employee)
    if doc.meta.has_field("employment_contract"):
        doc.employment_contract = contract
    onboarding, onboarding_created, warning = create_or_link_onboarding(doc, employee, contract)
    if onboarding and doc.meta.has_field("onboarding"):
        doc.onboarding = onboarding
    if warning and doc.meta.has_field("lifecycle_warnings"):
        doc.lifecycle_warnings = warning
    created = []
    if employee_created: created.append("Employee")
    if contract_created: created.append("Contract")
    if onboarding_created: created.append("Employee Onboarding")
    doc.flags.qorg_lifecycle_result = CommencementResult(employee, contract, onboarding, created, [warning] if warning else []).as_dict()
    return doc.flags.qorg_lifecycle_result


def finalize_commencement(doc, method=None):
    """Write final source links without silently overwriting later lifecycle decisions."""
    if not doc.employee:
        frappe.throw(_("Employee must be created or linked before submission."))
    employee = frappe.get_doc("Employee", doc.employee)
    updates = {}
    if not employee.get("date_of_joining"):
        updates["date_of_joining"] = doc.actual_commencement_date
    links = {
        "qorg_work_commencement_notice": doc.name,
        "qorg_appointment_letter": doc.appointment_letter,
        "qorg_job_applicant": doc.job_applicant,
        "qorg_employment_contract": doc.get("employment_contract"),
    }
    for fieldname, value in links.items():
        if value and employee.meta.has_field(fieldname) and not employee.get(fieldname):
            updates[fieldname] = value
    dates = {
        "qorg_employment_effective_date": doc.actual_commencement_date,
        "qorg_payroll_effective_date": doc.payroll_effective_date,
        "qorg_attendance_effective_date": doc.attendance_effective_date,
    }
    for fieldname, value in dates.items():
        if value and employee.meta.has_field(fieldname) and not employee.get(fieldname):
            updates[fieldname] = value
    if updates:
        frappe.db.set_value("Employee", employee.name, updates, update_modified=False)
    if doc.job_applicant and frappe.db.exists("Job Applicant", doc.job_applicant):
        _safe_status_update(doc.job_applicant, "Employment Commenced", "Complete Employee Onboarding")


def _validate_commencement_gate(doc):
    if doc.status != "Commenced":
        frappe.throw(_("Only a Commenced notice can create or link an Employee."))
    if not doc.actual_commencement_date:
        frappe.throw(_("Actual Commencement Date is required."))
    if not doc.appointment_letter:
        frappe.throw(_("Appointment Letter is required."))
    if not doc.company:
        frappe.throw(_("Company is required."))


def create_or_link_employee_from_commencement(doc):
    linked = _unique_existing_employee(doc)
    if linked:
        _validate_employee_compatibility(doc, linked)
        return linked, False
    values = _employee_values(doc)
    employee = frappe.new_doc("Employee")
    _assign_known_fields(employee, values)
    missing = _missing_required_fields(employee)
    if missing:
        frappe.throw(_("Cannot create Employee. Complete these required values in the recruitment source: {0}").format(", ".join(missing)))
    employee.flags.qorg_from_commencement = True
    employee.insert(ignore_permissions=True)
    return employee.name, True


def _unique_existing_employee(doc):
    candidates = set()
    if doc.employee and frappe.db.exists("Employee", doc.employee):
        candidates.add(doc.employee)
    lookups = {
        "qorg_work_commencement_notice": doc.name if doc.name else None,
        "qorg_job_applicant": doc.job_applicant,
    }
    applicant = _get_optional_doc("Job Applicant", doc.job_applicant)
    external_person = applicant.get("qorg_external_person") if applicant else None
    if external_person:
        lookups["qorg_external_person"] = external_person
    meta = frappe.get_meta("Employee")
    for fieldname, value in lookups.items():
        if value and meta.has_field(fieldname):
            candidates.update(frappe.get_all("Employee", filters={fieldname: value}, pluck="name", limit=2))
    email = _first_value((applicant, "email_id"), (applicant, "email"), (applicant, "personal_email"))
    if email:
        for fieldname in ("personal_email", "company_email", "user_id"):
            if meta.has_field(fieldname):
                candidates.update(frappe.get_all("Employee", filters={fieldname: email}, pluck="name", limit=2))
    if len(candidates) > 1:
        frappe.throw(_("Multiple Employee records match this commencement: {0}. Resolve the duplicate before continuing.").format(", ".join(sorted(candidates))))
    return next(iter(candidates), None)


def _employee_values(doc):
    appointment = _get_optional_doc("Appointment Letter", doc.appointment_letter)
    offer = _get_optional_doc("Job Offer", doc.job_offer)
    applicant = _get_optional_doc("Job Applicant", doc.job_applicant)
    values = {
        "employee_name": _first_value((applicant, "applicant_name"), (applicant, "employee_name"), (appointment, "employee_name")),
        "first_name": _first_value((applicant, "first_name"), (applicant, "applicant_name")),
        "company": doc.company,
        "date_of_joining": doc.actual_commencement_date,
        "status": "Active",
        "designation": doc.designation or _first_value((appointment, "designation"), (offer, "designation")),
        "department": doc.department or _first_value((appointment, "department"), (offer, "department")),
        "reports_to": doc.reports_to,
        "branch": doc.branch,
        "gender": _first_value((applicant, "gender"), (appointment, "gender")),
        "date_of_birth": _first_value((applicant, "date_of_birth"), (appointment, "date_of_birth")),
        "personal_email": _first_value((applicant, "email_id"), (applicant, "email"), (applicant, "personal_email")),
        "cell_number": _first_value((applicant, "phone_number"), (applicant, "phone"), (applicant, "mobile_no")),
        "employment_type": _first_value((appointment, "employment_type"), (offer, "employment_type")),
        "qorg_job_applicant": doc.job_applicant,
        "qorg_appointment_letter": doc.appointment_letter,
        "qorg_work_commencement_notice": doc.name,
        "qorg_project": doc.project,
        "qorg_branch": doc.branch,
    }
    if applicant and applicant.meta.has_field("qorg_external_person"):
        values["qorg_external_person"] = applicant.qorg_external_person
    return values


def _validate_employee_compatibility(doc, employee_name):
    employee = frappe.get_doc("Employee", employee_name)
    conflicts = []
    for fieldname in ("company", "designation", "department", "reports_to"):
        source = doc.get(fieldname)
        current = employee.get(fieldname)
        if source and current and source != current:
            conflicts.append(_("{0}: Employee={1}, Commencement={2}").format(employee.meta.get_label(fieldname), current, source))
    if conflicts:
        frappe.throw(_("The linked Employee conflicts with the approved commencement: {0}").format("; ".join(conflicts)))


def create_or_link_employment_contract(doc, employee_name):
    if not frappe.db.exists("DocType", "Contract") or not frappe.db.exists("QOrg Contract Type", "Employment Contract"):
        return None, False
    filters = {"qorg_work_commencement_notice": doc.name, "docstatus": ["<", 2]}
    if frappe.get_meta("Contract").has_field("qorg_work_commencement_notice"):
        existing = frappe.db.get_value("Contract", filters, "name")
        if existing:
            return existing, False
    existing = frappe.db.get_value("Contract", {"qorg_employee": employee_name, "qorg_contract_type": "Employment Contract", "docstatus": ["<", 2]}, "name")
    if existing:
        return existing, False
    contract = frappe.new_doc("Contract")
    values = {
        "party_type": "Employee", "party_name": employee_name,
        "start_date": doc.actual_commencement_date,
        "qorg_contract_title": _("Employment Contract - {0}").format(employee_name),
        "qorg_contract_type": "Employment Contract", "qorg_company": doc.company,
        "qorg_employee": employee_name, "qorg_job_applicant": doc.job_applicant,
        "qorg_appointment_letter": doc.appointment_letter,
        "qorg_work_commencement_notice": doc.name,
        "qorg_designation": doc.designation, "qorg_project": doc.project,
        "qorg_cost_center": doc.cost_center, "qorg_branch": doc.branch,
        "qorg_payroll_effective_date": doc.payroll_effective_date,
        "qorg_attendance_effective_date": doc.attendance_effective_date,
        "qorg_lifecycle_status": "Under Review",
    }
    appointment = _get_optional_doc("Appointment Letter", doc.appointment_letter)
    months = cint(_first_value((appointment, "qorg_expected_contract_duration_months"), (appointment, "expected_contract_duration_months")) or 0)
    if months:
        values["end_date"] = add_months(doc.actual_commencement_date, months)
    else:
        values["qorg_open_ended"] = 1
    _assign_known_fields(contract, values)
    contract.insert(ignore_permissions=True)
    return contract.name, True


def create_or_link_onboarding(doc, employee_name, contract_name=None):
    if doc.onboarding and frappe.db.exists("Employee Onboarding", doc.onboarding):
        return doc.onboarding, False, None
    existing = frappe.db.get_value("Employee Onboarding", {"employee": employee_name, "docstatus": ["<", 2]}, "name")
    if existing:
        return existing, False, None
    onboarding = frappe.new_doc("Employee Onboarding")
    employee = frappe.get_doc("Employee", employee_name)
    values = {
        "employee": employee_name, "employee_name": employee.employee_name,
        "company": employee.company, "department": employee.department,
        "designation": employee.designation, "employee_grade": employee.get("grade"),
        "boarding_begins_on": doc.actual_commencement_date,
        "date_of_joining": doc.actual_commencement_date,
        "qorg_work_commencement_notice": doc.name,
        "qorg_employment_contract": contract_name,
        "qorg_job_applicant": doc.job_applicant,
        "qorg_appointment_letter": doc.appointment_letter,
        "qorg_project": doc.project, "qorg_branch": doc.branch,
        "qorg_cost_center": doc.cost_center,
    }
    _assign_known_fields(onboarding, values)
    missing = _missing_required_fields(onboarding)
    if missing:
        return None, False, _("Employee Onboarding was not created because these required defaults are missing: {0}").format(", ".join(missing))
    onboarding.insert(ignore_permissions=True)
    return onboarding.name, True, None


def _assign_known_fields(target, values):
    for fieldname, value in values.items():
        if value not in (None, "") and target.meta.has_field(fieldname):
            target.set(fieldname, value)


def _missing_required_fields(doc):
    missing = []
    for field in doc.meta.fields:
        if not field.reqd or field.read_only or field.fieldtype in {"Section Break", "Column Break", "HTML", "Button"}:
            continue
        if doc.get(field.fieldname) in (None, "", []):
            missing.append(field.label or field.fieldname)
    return missing


def _get_optional_doc(doctype, name):
    return frappe.get_doc(doctype, name) if name and frappe.db.exists(doctype, name) else None


def _first_value(*pairs):
    for doc, fieldname in pairs:
        if doc and doc.get(fieldname) not in (None, ""):
            return doc.get(fieldname)
    return None


def _safe_status_update(applicant, status, next_action):
    meta = frappe.get_meta("Job Applicant")
    values = {}
    if meta.has_field("qorg_selection_status"):
        values["qorg_selection_status"] = status
    if meta.has_field("qorg_next_action"):
        values["qorg_next_action"] = next_action
    if values:
        frappe.db.set_value("Job Applicant", applicant, values, update_modified=False)
