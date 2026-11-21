import importlib

import frappe


REQUIRED = (
    "Payroll Entry",
    "Salary Slip",
    "Salary Component",
    "Salary Component Account",
    "Additional Salary",
    "Timesheet",
    "Journal Entry",
    "Journal Entry Account",
    "GL Entry",
    "Payment Entry",
    "Project",
    "Funding Agreement",
    "Budget Line",
    "Workforce Funding Plan",
    "Payroll Cost Policy",
    "Payroll Allocation Run",
    "Monthly Effort Certification",
)

HOOKS = (
    "qorg.qorg.payroll_workforce_allocation.migration.migrate",
    "qorg.qorg.payroll_workforce_allocation.events.validate_payroll_entry",
    "qorg.qorg.payroll_workforce_allocation.events.salary_slip_on_submit",
    "qorg.qorg.payroll_workforce_allocation.events.salary_slip_on_cancel",
)


def _runtime_versions():
    versions = {}
    try:
        from frappe.utils.change_log import get_versions

        raw = get_versions() or []
        if isinstance(raw, dict):
            return raw
        for row in raw:
            if isinstance(row, dict):
                app = row.get("app") or row.get("name") or row.get("title")
                version = row.get("version") or row.get("branch")
                if app:
                    versions[str(app)] = version
    except Exception:
        pass

    for app in frappe.get_installed_apps() or []:
        try:
            module = importlib.import_module(app)
            version = getattr(module, "__version__", None)
            if version is None:
                version = frappe.db.get_value("Installed Application", app, "app_version")
            versions[app] = version
        except Exception as exc:
            versions[app] = f"Unavailable: {exc}"
    return versions


def _fields(doctype):
    if not frappe.db.exists("DocType", doctype):
        return {}
    return {
        field.fieldname: {
            "fieldtype": field.fieldtype,
            "options": field.options,
            "required": bool(field.reqd),
        }
        for field in frappe.get_meta(doctype).fields
    }


def _import(path):
    module_name, method_name = path.rsplit(".", 1)
    return callable(getattr(importlib.import_module(module_name), method_name, None))


def run_payroll_capability_audit():
    docs = {doctype: bool(frappe.db.exists("DocType", doctype)) for doctype in REQUIRED}
    hook_imports = {}
    blockers = []
    warnings = []

    for path in HOOKS:
        try:
            hook_imports[path] = _import(path)
        except Exception as exc:
            hook_imports[path] = False
            warnings.append(f"Hook import failed: {path}: {exc}")

    for doctype, exists in docs.items():
        if not exists:
            blockers.append(f"Missing DocType: {doctype}")

    if not all(hook_imports.values()):
        blockers.append("One or more payroll hooks cannot be imported")

    payroll_fields = _fields("Payroll Entry")
    posting_fields = [
        fieldname
        for fieldname in ("journal_entry", "accrual_jv", "salary_slip_journal_entry")
        if fieldname in payroll_fields
    ]
    if not posting_fields:
        warnings.append(
            "Payroll Entry has no direct accrual Journal Entry field. Runtime fallback lookup will be used."
        )

    if frappe.db.exists("DocType", "Accounting Dimension"):
        dimensions = frappe.get_all(
            "Accounting Dimension",
            fields=["name", "fieldname", "document_type", "disabled"],
            limit_page_length=0,
        )
    else:
        dimensions = []

    managed = {}
    for doctype in ("Company", "Payroll Entry", "Salary Slip", "Journal Entry"):
        managed[doctype] = frappe.get_all(
            "Custom Field",
            filters={"dt": doctype, "fieldname": ["like", "custom_payroll%"]},
            fields=[
                "name",
                "fieldname",
                "fieldtype",
                "options",
                "module",
                "is_system_generated",
            ],
            limit_page_length=0,
        )

    permissions = {}
    for doctype in (
        "Workforce Funding Plan",
        "Payroll Cost Policy",
        "Payroll Allocation Run",
        "Monthly Effort Certification",
    ):
        if frappe.db.exists("DocType", doctype):
            permissions[doctype] = [row.as_dict() for row in frappe.get_meta(doctype).permissions]

    return {
        "runtime_versions": _runtime_versions(),
        "required_doctypes": docs,
        "payroll_capabilities": payroll_fields,
        "salary_component_capabilities": _fields("Salary Component"),
        "additional_salary_capabilities": _fields("Additional Salary"),
        "timesheet_capabilities": _fields("Timesheet"),
        "accounting_dimensions": dimensions,
        "budget_capabilities": _fields("Budget Line"),
        "commitment_capabilities": {
            "commitment_entry": _fields("Commitment Entry"),
            "commitment_ledger": _fields("Commitment Ledger"),
            "reserved_adjustments": _fields("Reserved Adjustment"),
        },
        "funding_capabilities": {
            "funding_agreement": _fields("Funding Agreement"),
            "project_funding_source": _fields("Project Funding Source"),
            "project_closure": _fields("Project Closure"),
        },
        "payment_capabilities": _fields("Payment Entry"),
        "doctype_permissions": permissions,
        "custom_field_ownership": managed,
        "hook_imports": hook_imports,
        "payroll_entry_posting_fields": posting_fields,
        "blockers": blockers,
        "warnings": warnings,
        "ready_for_pilot": not blockers,
    }
