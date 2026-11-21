import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

CUSTOM_FIELDS = {'Company': [{'fieldname': 'custom_payroll_allocation_section',
              'label': 'Payroll Cost Allocation',
              'fieldtype': 'Section Break',
              'insert_after': 'default_payroll_payable_account',
              'collapsible': 0},
             {'fieldname': 'custom_enable_payroll_allocation',
              'label': 'Enable Payroll Cost Allocation',
              'fieldtype': 'Check',
              'default': '0',
              'insert_after': 'custom_payroll_allocation_section',
              'print_hide': 1},
             {'fieldname': 'custom_require_full_payroll_allocation',
              'label': 'Require Full Payroll Allocation',
              'fieldtype': 'Check',
              'default': '1',
              'depends_on': 'eval:doc.custom_enable_payroll_allocation',
              'mandatory_depends_on': 'eval:doc.custom_enable_payroll_allocation',
              'insert_after': 'custom_enable_payroll_allocation',
              'print_hide': 1},
             {'fieldname': 'custom_payroll_allocation_column_2',
              'fieldtype': 'Column Break',
              'insert_after': 'custom_require_full_payroll_allocation'},
             {'fieldname': 'custom_payroll_allocation_clearing_account',
              'label': 'Payroll Allocation Clearing Account',
              'fieldtype': 'Link',
              'options': 'Account',
              'depends_on': 'eval:doc.custom_enable_payroll_allocation',
              'insert_after': 'custom_payroll_allocation_column_2',
              'print_hide': 1},
             {'fieldname': 'custom_payroll_allocation_rounding_account',
              'label': 'Payroll Allocation Rounding Account',
              'fieldtype': 'Link',
              'options': 'Account',
              'depends_on': 'eval:doc.custom_enable_payroll_allocation',
              'insert_after': 'custom_payroll_allocation_clearing_account',
              'print_hide': 1},
             {'fieldname': 'custom_payroll_liability_section',
              'label': 'Payroll Liabilities and Disclosure',
              'fieldtype': 'Section Break',
              'depends_on': 'eval:doc.custom_enable_payroll_allocation',
              'insert_after': 'custom_payroll_allocation_rounding_account'},
             {'fieldname': 'custom_payroll_liability_allocation_policy',
              'label': 'Payroll Liability Allocation Policy',
              'fieldtype': 'Select',
              'options': 'Do Not Split\nSplit Statutory Liabilities\nSplit Selected Liabilities\nSplit All Payroll Liabilities',
              'default': 'Do Not Split',
              'depends_on': 'eval:doc.custom_enable_payroll_allocation',
              'insert_after': 'custom_payroll_liability_section',
              'print_hide': 1},
             {'fieldname': 'custom_enforce_liability_dimensions_on_payment',
              'label': 'Enforce Liability Dimensions on Payment',
              'fieldtype': 'Check',
              'default': '0',
              'depends_on': 'eval:doc.custom_enable_payroll_allocation && doc.custom_payroll_liability_allocation_policy && '
                            'doc.custom_payroll_liability_allocation_policy!="Do Not Split"',
              'insert_after': 'custom_payroll_liability_allocation_policy',
              'print_hide': 1},
             {'fieldname': 'custom_payroll_liability_column_2',
              'fieldtype': 'Column Break',
              'insert_after': 'custom_enforce_liability_dimensions_on_payment'},
             {'fieldname': 'custom_employee_funding_disclosure_level',
              'label': 'Employee Funding Disclosure Level',
              'fieldtype': 'Select',
              'options': 'None\nProject and Percentage\nProject, Funding and Percentage\nFull Authorized Disclosure',
              'default': 'Project and Percentage',
              'depends_on': 'eval:doc.custom_enable_payroll_allocation',
              'insert_after': 'custom_payroll_liability_column_2',
              'print_hide': 1}],
 'Payroll Entry': [{'fieldname': 'custom_payroll_control_section',
                    'label': 'Payroll Allocation Control',
                    'fieldtype': 'Section Break',
                    'insert_after': 'status',
                    'collapsible': 1},
                   {'fieldname': 'custom_payroll_preflight_status',
                    'label': 'Payroll Preflight Status',
                    'fieldtype': 'Select',
                    'options': 'Not Run\nPassed\nWarnings\nBlocked',
                    'default': 'Not Run',
                    'read_only': 1,
                    'allow_on_submit': 1,
                    'no_copy': 1,
                    'print_hide': 1,
                    'insert_after': 'custom_payroll_control_section'},
                   {'fieldname': 'custom_payroll_allocation_status',
                    'label': 'Payroll Allocation Status',
                    'fieldtype': 'Select',
                    'options': 'Pending\nCalculated\nApproved\nPosted\nReconciled\nReversed\nCancelled',
                    'default': 'Pending',
                    'read_only': 1,
                    'allow_on_submit': 1,
                    'no_copy': 1,
                    'print_hide': 1,
                    'insert_after': 'custom_payroll_preflight_status'},
                   {'fieldname': 'custom_payroll_control_column_2',
                    'fieldtype': 'Column Break',
                    'insert_after': 'custom_payroll_allocation_status'},
                   {'fieldname': 'custom_payroll_allocation_run',
                    'label': 'Payroll Allocation Run',
                    'fieldtype': 'Link',
                    'options': 'Payroll Allocation Run',
                    'read_only': 1,
                    'allow_on_submit': 1,
                    'no_copy': 1,
                    'print_hide': 1,
                    'insert_after': 'custom_payroll_control_column_2'}],
 'Salary Slip': [{'fieldname': 'custom_payroll_allocation_section',
                  'label': 'Payroll Allocation',
                  'fieldtype': 'Section Break',
                  'insert_after': 'status',
                  'collapsible': 1},
                 {'fieldname': 'custom_payroll_allocation_status',
                  'label': 'Payroll Allocation Status',
                  'fieldtype': 'Select',
                  'options': 'Not Required\nPending\nCalculated\nApproved\nPosted\nReconciled\nReversed\nCancelled',
                  'default': 'Pending',
                  'read_only': 1,
                  'allow_on_submit': 1,
                  'no_copy': 1,
                  'print_hide': 1,
                  'insert_after': 'custom_payroll_allocation_section'},
                 {'fieldname': 'custom_payroll_allocation_column_2',
                  'fieldtype': 'Column Break',
                  'insert_after': 'custom_payroll_allocation_status'},
                 {'fieldname': 'custom_payroll_allocation_run',
                  'label': 'Payroll Allocation Run',
                  'fieldtype': 'Link',
                  'options': 'Payroll Allocation Run',
                  'read_only': 1,
                  'allow_on_submit': 1,
                  'no_copy': 1,
                  'print_hide': 1,
                  'insert_after': 'custom_payroll_allocation_column_2'},
                 {'fieldname': 'custom_payroll_allocation_summary_section',
                  'label': 'Workforce Funding Allocation',
                  'fieldtype': 'Section Break',
                  'insert_after': 'custom_payroll_allocation_run',
                  'collapsible': 1},
                 {'fieldname': 'custom_payroll_allocation_summary',
                  'label': 'Workforce Funding Allocation',
                  'fieldtype': 'HTML',
                  'read_only': 1,
                  'print_hide': 1,
                  'insert_after': 'custom_payroll_allocation_summary_section'}],
 'Journal Entry': [{'fieldname': 'custom_payroll_allocation_section',
                    'label': 'Payroll Allocation Reference',
                    'fieldtype': 'Section Break',
                    'insert_after': 'payroll_entry',
                    'depends_on': 'eval:doc.custom_payroll_allocation_run',
                    'collapsible': 1},
                   {'fieldname': 'custom_payroll_allocation_run',
                    'label': 'Payroll Allocation Run',
                    'fieldtype': 'Link',
                    'options': 'Payroll Allocation Run',
                    'read_only': 1,
                    'allow_on_submit': 1,
                    'no_copy': 1,
                    'print_hide': 1,
                    'insert_after': 'custom_payroll_allocation_section'}]}

def _provision_print_format():
    name = "Salary Slip and Workforce Funding Statement"
    template = frappe.get_app_path("qorg", "printing", "templates", "salary_slip_workforce_funding_statement.html")
    content = open(template, encoding="utf-8").read()
    if frappe.db.exists("Print Format", name):
        existing=frappe.get_doc("Print Format",name)
        if existing.module=="QOrg" and existing.doc_type=="Salary Slip" and existing.html!=content:
            frappe.db.set_value("Print Format",name,{"html":content,"print_format_type":"Jinja","custom_format":1,"disabled":0},update_modified=False)
        return
    frappe.get_doc({"doctype": "Print Format", "name": name, "doc_type": "Salary Slip", "module": "QOrg", "standard": "No", "print_format_type": "Jinja", "html": content, "custom_format": 1, "disabled": 0}).insert(ignore_permissions=True)


def provision_payroll_workforce_allocation():
    
    for definitions in CUSTOM_FIELDS.values():
        for definition in definitions:
            definition.setdefault("module", "QOrg")
            definition.setdefault("is_system_generated", 1)
    for dt,definitions in CUSTOM_FIELDS.items():
        for definition in definitions:
            name=f"{dt}-{definition['fieldname']}"
            if frappe.db.exists("Custom Field",name):
                existing=frappe.get_doc("Custom Field",name)
                if existing.module != "QOrg" or not existing.get("is_system_generated"):
                    frappe.throw(f"Managed Custom Field ownership conflict: {name}")
                if existing.fieldtype!=definition.get("fieldtype") or (definition.get("options") and existing.options!=definition.get("options")):
                    frappe.throw(f"Managed Custom Field definition conflict: {name}")
    create_custom_fields(CUSTOM_FIELDS, update=True)
    _provision_print_format()
    for doctype in CUSTOM_FIELDS:
        frappe.clear_cache(doctype=doctype)

def _ensure_roles():
    for role in ("Payroll Manager","Payroll User","Grant Manager","Projects Manager","Auditor"):
        if not frappe.db.exists("Role",role): frappe.get_doc({"doctype":"Role","role_name":role}).insert(ignore_permissions=True)

def _ensure_workspace_links():
    # Navigation is managed by the central QOrg navigation provisioner.
    return

def _ensure_indexes():
    for doctype,fields in (("Payroll Allocation Run",["payroll_entry"]),("Workforce Funding Plan",["employee","effective_from","effective_to"]),("Payroll Cost Policy",["company","funding_agreement","effective_from","effective_to"]),("Payroll Allocation Result",["salary_slip","salary_component","project"]),("Monthly Effort Certification",["employee","start_date","end_date"])):
        if frappe.db.exists("DocType",doctype): frappe.db.add_index(doctype,fields,index_name=f"idx_{frappe.scrub(doctype)}_{'_'.join(fields)}"[:60])

_original_provision = provision_payroll_workforce_allocation
def provision_payroll_workforce_allocation():
    _original_provision()
    _ensure_roles()
    _ensure_workspace_links()
    _ensure_indexes()
