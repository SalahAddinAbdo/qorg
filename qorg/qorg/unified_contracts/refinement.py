from __future__ import annotations

import frappe
from qorg.qorg.enterprise_foundation.idempotent_provisioning import create_custom_fields_if_changed

PROCUREMENT_CATEGORIES = ["Procurement", "Supply", "Service", "Works", "Consultancy", "Framework Agreement"]
HR_CATEGORIES = ["Employment", "Volunteer", "Internship", "Consultancy"]

CONTRACT_REFINEMENT_FIELDS = [
    {"fieldname":"qorg_party_model","label":"Party Model","fieldtype":"Data","insert_after":"qorg_contract_type","read_only":1,"fetch_from":"qorg_contract_type.party_model"},
    {"fieldname":"qorg_contract_parties","label":"Contract Parties","fieldtype":"Table","options":"QOrg Contract Party","insert_after":"qorg_counterparty","depends_on":"eval:doc.qorg_party_model=='Multiple Parties'","mandatory_depends_on":"eval:doc.qorg_party_model=='Multiple Parties'"},
    {"fieldname":"qorg_open_ended","label":"Open-ended Contract","fieldtype":"Check","default":"0","insert_after":"end_date"},
    {"fieldname":"qorg_default_values_applied","label":"Default Values Applied","fieldtype":"Check","default":"0","hidden":1,"read_only":1,"insert_after":"qorg_template_copied_on"},
    {"fieldname":"qorg_deliverables","label":"Deliverables","fieldtype":"Table","options":"Deliverable Requirement","insert_after":"qorg_milestones","depends_on":"eval:doc.qorg_category && !doc.qorg_is_zero_value"},
    {"fieldname":"qorg_required_documents","label":"Required Documents","fieldtype":"Table","options":"Supporting Document Row","insert_after":"qorg_guarantees"},
]

TEMPLATE_REFINEMENT_FIELDS = [
    {"fieldname":"qorg_category","label":"Contract Category","fieldtype":"Data","insert_after":"qorg_contract_type","read_only":1,"fetch_from":"qorg_contract_type.category"},
    {"fieldname":"qorg_party_model","label":"Party Model","fieldtype":"Data","insert_after":"qorg_category","read_only":1,"fetch_from":"qorg_contract_type.party_model"},
    {"fieldname":"qorg_defaults_section","label":"Contract Defaults","fieldtype":"Section Break","insert_after":"qorg_changes_require_legal_review"},
    {"fieldname":"qorg_company","label":"Company","fieldtype":"Link","options":"Company","insert_after":"qorg_defaults_section"},
    {"fieldname":"qorg_owning_department","label":"Owning Department","fieldtype":"Link","options":"Department","insert_after":"qorg_company"},
    {"fieldname":"qorg_contract_manager","label":"Default Contract Manager","fieldtype":"Link","options":"User","insert_after":"qorg_owning_department"},
    {"fieldname":"qorg_legal_owner","label":"Default Legal Owner","fieldtype":"Link","options":"User","insert_after":"qorg_contract_manager"},
    {"fieldname":"qorg_defaults_column","fieldtype":"Column Break","insert_after":"qorg_legal_owner"},
    {"fieldname":"qorg_confidential","label":"Confidential by Default","fieldtype":"Check","default":"0","insert_after":"qorg_defaults_column"},
    {"fieldname":"qorg_contract_purpose","label":"Default Contract Purpose","fieldtype":"Small Text","insert_after":"qorg_confidential"},
    {"fieldname":"qorg_default_party_doctype","label":"Default Extended Party Type","fieldtype":"Link","options":"DocType","insert_after":"qorg_contract_purpose","depends_on":"eval:['Extended Party','Either Standard or Extended'].includes(doc.qorg_party_model)"},
    {"fieldname":"qorg_duration_section","label":"Duration and Renewal Defaults","fieldtype":"Section Break","insert_after":"qorg_default_party_doctype"},
    {"fieldname":"qorg_default_duration_months","label":"Default Duration (Months)","fieldtype":"Int","non_negative":1,"insert_after":"qorg_duration_section"},
    {"fieldname":"qorg_allow_open_ended","label":"Allow Open-ended Period","fieldtype":"Check","default":"0","insert_after":"qorg_default_duration_months"},
    {"fieldname":"qorg_auto_renewal","label":"Auto Renewal by Default","fieldtype":"Check","default":"0","insert_after":"qorg_allow_open_ended"},
    {"fieldname":"qorg_duration_column","fieldtype":"Column Break","insert_after":"qorg_auto_renewal"},
    {"fieldname":"qorg_renewal_notice_days","label":"Default Renewal Notice (Days)","fieldtype":"Int","non_negative":1,"insert_after":"qorg_duration_column"},
    {"fieldname":"qorg_termination_notice_days","label":"Default Termination Notice (Days)","fieldtype":"Int","non_negative":1,"insert_after":"qorg_renewal_notice_days"},
    {"fieldname":"qorg_financial_defaults_section","label":"Financial Defaults","fieldtype":"Section Break","insert_after":"qorg_termination_notice_days","depends_on":"eval:doc.qorg_contract_type"},
    {"fieldname":"qorg_currency","label":"Default Currency","fieldtype":"Link","options":"Currency","insert_after":"qorg_financial_defaults_section"},
    {"fieldname":"qorg_payment_basis","label":"Default Payment Basis","fieldtype":"Select","options":"\nFixed Price\nTime and Materials\nMilestone\nUnit Rate\nSalary / Payroll\nAllowance\nCost Reimbursement\nFramework Ceiling\nNo Payment\nOther","insert_after":"qorg_currency"},
    {"fieldname":"qorg_is_zero_value","label":"Zero-value Contract by Default","fieldtype":"Check","default":"0","insert_after":"qorg_payment_basis"},
    {"fieldname":"qorg_advance_payment_percent","label":"Default Advance Payment Percent","fieldtype":"Percent","insert_after":"qorg_is_zero_value"},
    {"fieldname":"qorg_financial_defaults_column","fieldtype":"Column Break","insert_after":"qorg_advance_payment_percent"},
    {"fieldname":"qorg_retention_percent","label":"Default Retention Percent","fieldtype":"Percent","insert_after":"qorg_financial_defaults_column"},
    {"fieldname":"qorg_liquidated_damages_percent","label":"Default Liquidated Damages Percent","fieldtype":"Percent","insert_after":"qorg_retention_percent"},
    {"fieldname":"qorg_ceiling_policy","label":"Default Ceiling Policy","fieldtype":"Select","options":"\nNot Applicable\nEqual to Contract Value\nManual Ceiling Required\nFramework Ceiling","insert_after":"qorg_liquidated_damages_percent"},
    {"fieldname":"qorg_execution_section","label":"Execution Defaults","fieldtype":"Section Break","insert_after":"qorg_ceiling_policy","collapsible":1},
    {"fieldname":"qorg_milestones","label":"Default Milestones","fieldtype":"Table","options":"Contract Milestone","insert_after":"qorg_execution_section"},
    {"fieldname":"qorg_deliverables","label":"Default Deliverables","fieldtype":"Table","options":"Deliverable Requirement","insert_after":"qorg_milestones"},
    {"fieldname":"qorg_guarantees","label":"Default Guarantees","fieldtype":"Table","options":"Guarantee Row","insert_after":"qorg_deliverables"},
    {"fieldname":"qorg_required_documents","label":"Default Required Documents","fieldtype":"Table","options":"Supporting Document Row","insert_after":"qorg_guarantees"},
    {"fieldname":"qorg_scope_of_work","label":"Default Scope of Work","fieldtype":"Text Editor","insert_after":"qorg_required_documents"},
    {"fieldname":"qorg_payment_terms","label":"Default Payment Terms","fieldtype":"Text Editor","insert_after":"qorg_scope_of_work"},
    {"fieldname":"qorg_termination_terms","label":"Default Termination Terms","fieldtype":"Text Editor","insert_after":"qorg_payment_terms"},
    {"fieldname":"qorg_approval_roles","label":"Required Approval Roles","fieldtype":"Table","options":"QOrg Contract Approval Role","insert_after":"qorg_termination_terms"},
    {"fieldname":"qorg_employment_section","label":"Employment Defaults","fieldtype":"Section Break","insert_after":"qorg_approval_roles","depends_on":"eval:doc.qorg_category=='Employment'","collapsible":1},
    {"fieldname":"qorg_employment_type","label":"Default Employment Type","fieldtype":"Link","options":"Employment Type","insert_after":"qorg_employment_section"},
    {"fieldname":"qorg_probation_months","label":"Default Probation (Months)","fieldtype":"Int","non_negative":1,"insert_after":"qorg_employment_type"},
    {"fieldname":"qorg_payroll_activation_required","label":"Payroll Activation Required","fieldtype":"Check","default":"1","insert_after":"qorg_probation_months"},
    {"fieldname":"qorg_attendance_activation_required","label":"Attendance Activation Required","fieldtype":"Check","default":"1","insert_after":"qorg_payroll_activation_required"},
    {"fieldname":"qorg_leave_activation_required","label":"Leave Activation Required","fieldtype":"Check","default":"1","insert_after":"qorg_attendance_activation_required"},
    {"fieldname":"qorg_employment_column","fieldtype":"Column Break","insert_after":"qorg_leave_activation_required"},
    {"fieldname":"qorg_bank_details_required","label":"Bank Details Required","fieldtype":"Check","default":"1","insert_after":"qorg_employment_column"},
    {"fieldname":"qorg_salary_assignment_required","label":"Salary Structure Assignment Required","fieldtype":"Check","default":"1","insert_after":"qorg_bank_details_required"},
    {"fieldname":"qorg_work_commencement_required","label":"Work Commencement Notice Required","fieldtype":"Check","default":"1","insert_after":"qorg_salary_assignment_required"},
    {"fieldname":"qorg_onboarding_required","label":"Employee Onboarding Required","fieldtype":"Check","default":"1","insert_after":"qorg_work_commencement_required"},
    {"fieldname":"qorg_participation_section","label":"Volunteer and Internship Defaults","fieldtype":"Section Break","insert_after":"qorg_onboarding_required","depends_on":"eval:['Volunteer','Internship'].includes(doc.qorg_category)","collapsible":1},
    {"fieldname":"qorg_participation_required","label":"Participation Engagement Required","fieldtype":"Check","default":"1","insert_after":"qorg_participation_section"},
    {"fieldname":"qorg_supervisor_required","label":"Supervisor Required","fieldtype":"Check","default":"1","insert_after":"qorg_participation_required"},
    {"fieldname":"qorg_expected_hours_required","label":"Expected Hours Required","fieldtype":"Check","default":"1","insert_after":"qorg_supervisor_required"},
    {"fieldname":"qorg_participation_column","fieldtype":"Column Break","insert_after":"qorg_expected_hours_required"},
    {"fieldname":"qorg_allowance_applicable","label":"Allowance Applicable","fieldtype":"Check","default":"0","insert_after":"qorg_participation_column"},
    {"fieldname":"qorg_safeguarding_required","label":"Safeguarding / PSEA Required","fieldtype":"Check","default":"1","insert_after":"qorg_allowance_applicable"},
    {"fieldname":"qorg_confidentiality_required","label":"Confidentiality Agreement Required","fieldtype":"Check","default":"1","insert_after":"qorg_safeguarding_required"},
]


def provision_refinement_fields():
    definitions = {}
    if frappe.db.exists("DocType", "Contract"):
        definitions["Contract"] = CONTRACT_REFINEMENT_FIELDS
    if frappe.db.exists("DocType", "Contract Template"):
        definitions["Contract Template"] = TEMPLATE_REFINEMENT_FIELDS
    if definitions:
        create_custom_fields_if_changed(definitions, update=True)
