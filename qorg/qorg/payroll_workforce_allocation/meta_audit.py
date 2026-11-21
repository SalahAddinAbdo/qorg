import importlib,frappe
REQUIRED=("Payroll Entry","Salary Slip","Salary Component","Salary Component Account","Additional Salary","Timesheet","Journal Entry","Journal Entry Account","GL Entry","Payment Entry","Project","Funding Agreement","Budget Line","Workforce Funding Plan","Payroll Cost Policy","Payroll Allocation Run","Monthly Effort Certification")
HOOKS=("qorg.qorg.payroll_workforce_allocation.migration.migrate","qorg.qorg.payroll_workforce_allocation.events.validate_payroll_entry","qorg.qorg.payroll_workforce_allocation.events.salary_slip_on_submit","qorg.qorg.payroll_workforce_allocation.events.salary_slip_on_cancel")
def _fields(dt):
    if not frappe.db.exists("DocType",dt): return {}
    return {x.fieldname:{"fieldtype":x.fieldtype,"options":x.options,"required":bool(x.reqd)} for x in frappe.get_meta(dt).fields}
def _import(path): module,name=path.rsplit(".",1);return callable(getattr(importlib.import_module(module),name,None))
def run_payroll_capability_audit():
    docs={x:bool(frappe.db.exists("DocType",x)) for x in REQUIRED};hooks={};blockers=[]
    for path in HOOKS:
        try:hooks[path]=_import(path)
        except Exception as e:hooks[path]=False
    for x,ok in docs.items():
        if not ok:blockers.append(f"Missing DocType: {x}")
    if not all(hooks.values()):blockers.append("One or more payroll hooks cannot be imported")
    payroll=_fields("Payroll Entry");posting=[x for x in ("journal_entry","accrual_jv","salary_slip_journal_entry") if x in payroll]
    if not posting:blockers.append("Payroll accrual Journal Entry field was not identified")
    dimensions=frappe.get_all("Accounting Dimension",fields=["name","fieldname","document_type","disabled"],limit_page_length=0) if frappe.db.exists("DocType","Accounting Dimension") else []
    managed={};
    for dt in ("Company","Payroll Entry","Salary Slip","Journal Entry"):
        managed[dt]=frappe.get_all("Custom Field",filters={"dt":dt,"fieldname":["like","custom_payroll%"]},fields=["name","fieldname","fieldtype","options","module","is_system_generated"],limit_page_length=0)
    return {"runtime_versions":frappe.get_versions() or {},"required_doctypes":docs,"payroll_capabilities":payroll,"salary_component_capabilities":_fields("Salary Component"),"additional_salary_capabilities":_fields("Additional Salary"),"timesheet_capabilities":_fields("Timesheet"),"accounting_dimensions":dimensions,"budget_capabilities":_fields("Budget Line"),"commitment_capabilities":{"commitment_entry":_fields("Commitment Entry"),"commitment_ledger":_fields("Commitment Ledger"),"reserved_adjustments":_fields("Reserved Adjustment")},"funding_capabilities":{"funding_agreement":_fields("Funding Agreement"),"project_funding_source":_fields("Project Funding Source"),"project_closure":_fields("Project Closure")},"payment_capabilities":_fields("Payment Entry"),"doctype_permissions":{dt:[x.as_dict() for x in frappe.get_meta(dt).permissions] for dt in ("Workforce Funding Plan","Payroll Cost Policy","Payroll Allocation Run","Monthly Effort Certification") if frappe.db.exists("DocType",dt)},"custom_field_ownership":managed,"hook_imports":hooks,"payroll_entry_posting_fields":posting,"blockers":blockers,"warnings":[],"ready_for_pilot":not blockers}
