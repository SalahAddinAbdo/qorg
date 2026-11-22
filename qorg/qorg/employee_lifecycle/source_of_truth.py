"""Authoritative ownership and precedence rules for employee-lifecycle data."""

FIELD_POLICY = {
    "company": {"owner": "Employee", "initial_precedence": ["Work Commencement Notice", "Appointment Letter", "Job Offer", "Job Opening"], "change_via": "Employee Transfer"},
    "branch": {"owner": "Employee", "initial_precedence": ["Work Commencement Notice", "Appointment Letter", "Job Offer"], "change_via": "Employee Transfer"},
    "department": {"owner": "Employee", "initial_precedence": ["Work Commencement Notice", "Appointment Letter", "Job Offer"], "change_via": "Employee Transfer"},
    "designation": {"owner": "Employee", "initial_precedence": ["Work Commencement Notice", "Appointment Letter", "Job Offer", "Job Opening"], "change_via": "Employee Promotion"},
    "reports_to": {"owner": "Employee", "initial_precedence": ["Work Commencement Notice", "Appointment Letter"], "change_via": "Employee Transfer"},
    "employment_type": {"owner": "Employee", "initial_precedence": ["Contract", "Appointment Letter", "Job Offer"], "change_via": "Employee Transfer or Contract Amendment"},
    "date_of_joining": {"owner": "Employee", "initial_precedence": ["Work Commencement Notice"], "change_via": "Approved lifecycle correction"},
    "contract_period": {"owner": "Contract", "initial_precedence": ["Contract", "Appointment Letter"], "change_via": "Contract Amendment"},
    "salary_structure": {"owner": "Salary Structure Assignment", "initial_precedence": ["Salary Structure Assignment"], "change_via": "New Salary Structure Assignment"},
    "funding_allocation": {"owner": "Workforce Funding Plan", "initial_precedence": ["Workforce Funding Plan"], "change_via": "Superseding Workforce Funding Plan"},
    "cost_center": {"owner": "Employee", "initial_precedence": ["Work Commencement Notice", "Appointment Letter"], "change_via": "Employee Transfer"},
    "payroll_effective_date": {"owner": "Employee", "initial_precedence": ["Work Commencement Notice", "Contract"], "change_via": "Service Activation"},
    "attendance_effective_date": {"owner": "Employee", "initial_precedence": ["Work Commencement Notice", "Contract"], "change_via": "Service Activation"},
    "leave_effective_date": {"owner": "Employee", "initial_precedence": ["Contract", "Employee"], "change_via": "Service Activation"},
    "holiday_list": {"owner": "Employee", "initial_precedence": ["Employee", "Company"], "change_via": "Employee or Holiday List Assignment"},
    "leave_policy": {"owner": "Leave Policy Assignment", "initial_precedence": ["Leave Policy Assignment"], "change_via": "New Leave Policy Assignment"},
    "shift": {"owner": "Shift Assignment", "initial_precedence": ["Shift Assignment", "Employee"], "change_via": "Shift Assignment"},
}

LOCKED_AFTER_EMPLOYEE_CREATION = {"company", "branch", "department", "designation", "reports_to", "employment_type", "cost_center"}


def get_policy(fieldname=None):
    if fieldname:
        return FIELD_POLICY.get(fieldname)
    return FIELD_POLICY
