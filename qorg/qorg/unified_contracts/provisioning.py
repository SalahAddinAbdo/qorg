from __future__ import annotations

import frappe
from qorg.qorg.enterprise_foundation.idempotent_provisioning import create_custom_fields_if_changed

CONTRACT_FIELDS = [
    {"fieldname":"qorg_contract_identity_section","label":"QOrg Contract Classification","fieldtype":"Section Break","insert_after":"party_user"},
    {"fieldname":"qorg_contract_title","label":"Contract Title","fieldtype":"Data","insert_after":"qorg_contract_identity_section","in_list_view":1,"in_standard_filter":1,"translatable":1},
    {"fieldname":"qorg_contract_type","label":"Contract Type","fieldtype":"Link","options":"QOrg Contract Type","insert_after":"qorg_contract_title","in_list_view":1,"in_standard_filter":1},
    {"fieldname":"qorg_category","label":"Contract Category","fieldtype":"Data","insert_after":"qorg_contract_type","read_only":1,"fetch_from":"qorg_contract_type.category","in_standard_filter":1},
    {"fieldname":"qorg_lifecycle_status","label":"Lifecycle Status","fieldtype":"Select","options":"Draft\nUnder Review\nPending Approval\nApproved\nPending Signature\nActive\nSuspended\nExpiring\nExpired\nCompleted\nTerminated\nCancelled\nSuperseded","default":"Draft","insert_after":"qorg_category","in_list_view":1,"in_standard_filter":1,"allow_on_submit":1},
    {"fieldname":"qorg_identity_column","fieldtype":"Column Break","insert_after":"qorg_lifecycle_status"},
    {"fieldname":"qorg_company","label":"Company","fieldtype":"Link","options":"Company","insert_after":"qorg_identity_column","in_standard_filter":1},
    {"fieldname":"qorg_contract_number","label":"External Contract Number","fieldtype":"Data","insert_after":"qorg_company","unique":1},
    {"fieldname":"qorg_contract_purpose","label":"Contract Purpose","fieldtype":"Small Text","insert_after":"qorg_contract_number"},
    {"fieldname":"qorg_confidential","label":"Confidential Contract","fieldtype":"Check","default":"0","insert_after":"qorg_contract_purpose"},
    {"fieldname":"qorg_counterparty_section","label":"Extended Counterparty","fieldtype":"Section Break","insert_after":"qorg_confidential","collapsible":1},
    {"fieldname":"qorg_counterparty_doctype","label":"Extended Party Type","fieldtype":"Link","options":"DocType","insert_after":"qorg_counterparty_section","description":"Use only when the legal counterparty is not Customer, Supplier, or Employee."},
    {"fieldname":"qorg_counterparty","label":"Extended Party","fieldtype":"Dynamic Link","options":"qorg_counterparty_doctype","insert_after":"qorg_counterparty_doctype"},
    {"fieldname":"qorg_ownership_section","label":"Ownership and Accounting Context","fieldtype":"Section Break","insert_after":"qorg_counterparty","collapsible":1},
    {"fieldname":"qorg_owning_department","label":"Owning Department","fieldtype":"Link","options":"Department","insert_after":"qorg_ownership_section"},
    {"fieldname":"qorg_contract_manager","label":"Contract Manager","fieldtype":"Link","options":"User","insert_after":"qorg_owning_department"},
    {"fieldname":"qorg_legal_owner","label":"Legal Owner / Reviewer","fieldtype":"Link","options":"User","insert_after":"qorg_contract_manager"},
    {"fieldname":"qorg_ownership_column","fieldtype":"Column Break","insert_after":"qorg_legal_owner"},
    {"fieldname":"qorg_project","label":"Project","fieldtype":"Link","options":"Project","insert_after":"qorg_ownership_column"},
    {"fieldname":"qorg_cost_center","label":"Cost Center","fieldtype":"Link","options":"Cost Center","insert_after":"qorg_project"},
    {"fieldname":"qorg_branch","label":"Branch","fieldtype":"Link","options":"Branch","insert_after":"qorg_cost_center"},
    {"fieldname":"qorg_funding_agreement","label":"Funding Agreement","fieldtype":"Link","options":"Funding Agreement","insert_after":"qorg_branch"},
    {"fieldname":"qorg_budget_line","label":"Budget Line","fieldtype":"Link","options":"Budget Line","insert_after":"qorg_funding_agreement"},
    {"fieldname":"qorg_value_section","label":"Contract Value","fieldtype":"Section Break","insert_after":"end_date","collapsible":1},
    {"fieldname":"qorg_currency","label":"Currency","fieldtype":"Link","options":"Currency","insert_after":"qorg_value_section"},
    {"fieldname":"qorg_contract_value","label":"Contract Value","fieldtype":"Currency","options":"qorg_currency","insert_after":"qorg_currency"},
    {"fieldname":"qorg_ceiling_amount","label":"Ceiling Amount","fieldtype":"Currency","options":"qorg_currency","insert_after":"qorg_contract_value"},
    {"fieldname":"qorg_value_column","fieldtype":"Column Break","insert_after":"qorg_ceiling_amount"},
    {"fieldname":"qorg_is_zero_value","label":"Zero-value / Non-financial Contract","fieldtype":"Check","default":"0","insert_after":"qorg_value_column"},
    {"fieldname":"qorg_payment_basis","label":"Payment Basis","fieldtype":"Select","options":"\nFixed Price\nTime and Materials\nMilestone\nUnit Rate\nSalary / Payroll\nAllowance\nCost Reimbursement\nFramework Ceiling\nNo Payment\nOther","insert_after":"qorg_is_zero_value"},
    {"fieldname":"qorg_value_confidential","label":"Value Confidential","fieldtype":"Check","default":"0","insert_after":"qorg_payment_basis"},
    {"fieldname":"qorg_employment_section","label":"Employment Contract Details","fieldtype":"Section Break","insert_after":"qorg_value_confidential","depends_on":"eval:doc.qorg_category=='Employment'","collapsible":1},
    {"fieldname":"qorg_employee","label":"Employee","fieldtype":"Link","options":"Employee","insert_after":"qorg_employment_section"},
    {"fieldname":"qorg_job_applicant","label":"Job Applicant","fieldtype":"Link","options":"Job Applicant","insert_after":"qorg_employee"},
    {"fieldname":"qorg_appointment_letter","label":"Appointment Letter","fieldtype":"Link","options":"Appointment Letter","insert_after":"qorg_job_applicant"},
    {"fieldname":"qorg_work_commencement_notice","label":"Work Commencement Notice","fieldtype":"Link","options":"Work Commencement Notice","insert_after":"qorg_appointment_letter"},
    {"fieldname":"qorg_employment_column","fieldtype":"Column Break","insert_after":"qorg_work_commencement_notice"},
    {"fieldname":"qorg_employment_type","label":"Employment Type","fieldtype":"Link","options":"Employment Type","insert_after":"qorg_employment_column"},
    {"fieldname":"qorg_designation","label":"Designation","fieldtype":"Link","options":"Designation","insert_after":"qorg_employment_type"},
    {"fieldname":"qorg_employee_grade","label":"Employee Grade","fieldtype":"Link","options":"Employee Grade","insert_after":"qorg_designation"},
    {"fieldname":"qorg_probation_end_date","label":"Probation End Date","fieldtype":"Date","insert_after":"qorg_employee_grade"},
    {"fieldname":"qorg_payroll_effective_date","label":"Payroll Effective Date","fieldtype":"Date","insert_after":"qorg_probation_end_date"},
    {"fieldname":"qorg_attendance_effective_date","label":"Attendance Effective Date","fieldtype":"Date","insert_after":"qorg_payroll_effective_date"},
    {"fieldname":"qorg_leave_effective_date","label":"Leave Effective Date","fieldtype":"Date","insert_after":"qorg_attendance_effective_date"},
    {"fieldname":"qorg_participation_section","label":"Volunteer and Participation Details","fieldtype":"Section Break","insert_after":"qorg_leave_effective_date","depends_on":"eval:['Volunteer','Internship'].includes(doc.qorg_category)","collapsible":1},
    {"fieldname":"qorg_external_person","label":"External Person","fieldtype":"Link","options":"External Person","insert_after":"qorg_participation_section"},
    {"fieldname":"qorg_participation_engagement","label":"Participation Engagement","fieldtype":"Link","options":"Participation Engagement","insert_after":"qorg_external_person"},
    {"fieldname":"qorg_supervisor","label":"Supervisor","fieldtype":"Link","options":"Employee","insert_after":"qorg_participation_engagement"},
    {"fieldname":"qorg_service_location","label":"Service Location","fieldtype":"Data","insert_after":"qorg_supervisor"},
    {"fieldname":"qorg_expected_hours","label":"Expected Hours","fieldtype":"Float","insert_after":"qorg_service_location","non_negative":1},
    {"fieldname":"qorg_renewal_section","label":"Renewal, Amendment and Termination","fieldtype":"Section Break","insert_after":"qorg_expected_hours","collapsible":1},
    {"fieldname":"qorg_previous_contract","label":"Previous Contract","fieldtype":"Link","options":"Contract","insert_after":"qorg_renewal_section"},
    {"fieldname":"qorg_renewal_of","label":"Renewal Of","fieldtype":"Link","options":"Contract","insert_after":"qorg_previous_contract"},
    {"fieldname":"qorg_version_number","label":"Contract Version","fieldtype":"Int","default":"1","insert_after":"qorg_renewal_of","read_only":1},
    {"fieldname":"qorg_auto_renewal","label":"Auto Renewal","fieldtype":"Check","default":"0","insert_after":"qorg_version_number"},
    {"fieldname":"qorg_renewal_notice_days","label":"Renewal Notice (Days)","fieldtype":"Int","default":"30","insert_after":"qorg_auto_renewal","non_negative":1},
    {"fieldname":"qorg_renewal_column","fieldtype":"Column Break","insert_after":"qorg_renewal_notice_days"},
    {"fieldname":"qorg_termination_notice_days","label":"Termination Notice (Days)","fieldtype":"Int","default":"30","insert_after":"qorg_renewal_column","non_negative":1},
    {"fieldname":"qorg_termination_reason","label":"Termination Reason","fieldtype":"Small Text","insert_after":"qorg_termination_notice_days"},
    {"fieldname":"qorg_superseded_by","label":"Superseded By","fieldtype":"Link","options":"Contract","insert_after":"qorg_termination_reason","read_only":1},
    {"fieldname":"qorg_source_section","label":"Operational Source Links","fieldtype":"Section Break","insert_after":"qorg_superseded_by","collapsible":1},
    {"fieldname":"qorg_procurement_process","label":"Procurement Process","fieldtype":"Link","options":"Procurement Process","insert_after":"qorg_source_section"},
    {"fieldname":"qorg_award_decision","label":"Award Decision","fieldtype":"Link","options":"Award Decision","insert_after":"qorg_procurement_process"},
    {"fieldname":"qorg_procurement_details_section","label":"Procurement Performance and Payment","fieldtype":"Section Break","insert_after":"qorg_award_decision","depends_on":"eval:['Procurement','Supply','Service','Works','Consultancy','Framework Agreement'].includes(doc.qorg_category)","collapsible":1},
    {"fieldname":"qorg_technical_manager","label":"Technical Manager","fieldtype":"Link","options":"User","insert_after":"qorg_procurement_details_section"},
    {"fieldname":"qorg_advance_payment_percent","label":"Advance Payment Percent","fieldtype":"Percent","insert_after":"qorg_technical_manager"},
    {"fieldname":"qorg_retention_percent","label":"Retention Percent","fieldtype":"Percent","insert_after":"qorg_advance_payment_percent"},
    {"fieldname":"qorg_liquidated_damages_percent","label":"Liquidated Damages Percent","fieldtype":"Percent","insert_after":"qorg_retention_percent"},
    {"fieldname":"qorg_procurement_column","fieldtype":"Column Break","insert_after":"qorg_liquidated_damages_percent"},
    {"fieldname":"qorg_warranty_end_date","label":"Warranty End Date","fieldtype":"Date","insert_after":"qorg_procurement_column"},
    {"fieldname":"qorg_defects_liability_end_date","label":"Defects Liability End Date","fieldtype":"Date","insert_after":"qorg_warranty_end_date"},
    {"fieldname":"qorg_milestones_section","label":"Contract Milestones and Guarantees","fieldtype":"Section Break","insert_after":"qorg_defects_liability_end_date","collapsible":1},
    {"fieldname":"qorg_milestones","label":"Milestones","fieldtype":"Table","options":"Contract Milestone","insert_after":"qorg_milestones_section"},
    {"fieldname":"qorg_guarantees","label":"Guarantees","fieldtype":"Table","options":"Guarantee Row","insert_after":"qorg_milestones"},
    {"fieldname":"qorg_terms_section","label":"Operational Terms","fieldtype":"Section Break","insert_after":"qorg_guarantees","collapsible":1},
    {"fieldname":"qorg_scope_of_work","label":"Scope of Work","fieldtype":"Text Editor","insert_after":"qorg_terms_section"},
    {"fieldname":"qorg_payment_terms","label":"Payment Terms","fieldtype":"Text Editor","insert_after":"qorg_scope_of_work"},
    {"fieldname":"qorg_termination_terms","label":"Termination Terms","fieldtype":"Text Editor","insert_after":"qorg_payment_terms"},
    {"fieldname":"qorg_contract_document","label":"Signed Contract Document","fieldtype":"Attach","insert_after":"qorg_termination_terms"},
    {"fieldname":"qorg_financial_tracking_section","label":"Financial Tracking","fieldtype":"Section Break","insert_after":"qorg_contract_document","collapsible":1},
    {"fieldname":"qorg_advance_payment_amount","label":"Advance Payment Amount","fieldtype":"Currency","options":"qorg_currency","insert_after":"qorg_financial_tracking_section","read_only":1},
    {"fieldname":"qorg_advance_recovered_amount","label":"Advance Recovered Amount","fieldtype":"Currency","options":"qorg_currency","insert_after":"qorg_advance_payment_amount","read_only":1},
    {"fieldname":"qorg_retention_amount","label":"Retention Amount","fieldtype":"Currency","options":"qorg_currency","insert_after":"qorg_advance_recovered_amount","read_only":1},
    {"fieldname":"qorg_retention_released_amount","label":"Retention Released Amount","fieldtype":"Currency","options":"qorg_currency","insert_after":"qorg_retention_amount","read_only":1},
    {"fieldname":"qorg_financial_tracking_column","fieldtype":"Column Break","insert_after":"qorg_retention_released_amount"},
    {"fieldname":"qorg_invoiced_amount","label":"Invoiced Amount","fieldtype":"Currency","options":"qorg_currency","insert_after":"qorg_financial_tracking_column","read_only":1},
    {"fieldname":"qorg_paid_amount","label":"Paid Amount","fieldtype":"Currency","options":"qorg_currency","insert_after":"qorg_invoiced_amount","read_only":1},
    {"fieldname":"qorg_remaining_contract_value","label":"Remaining Contract Value","fieldtype":"Currency","options":"qorg_currency","insert_after":"qorg_paid_amount","read_only":1},
    {"fieldname":"qorg_template_section","label":"Template Governance","fieldtype":"Section Break","insert_after":"contract_terms","collapsible":1},
    {"fieldname":"qorg_template_version","label":"Template Version","fieldtype":"Int","insert_after":"qorg_template_section","read_only":1},
    {"fieldname":"qorg_template_snapshot_hash","label":"Template Snapshot Hash","fieldtype":"Data","insert_after":"qorg_template_version","read_only":1,"hidden":1},
    {"fieldname":"qorg_template_copied_on","label":"Template Copied On","fieldtype":"Datetime","insert_after":"qorg_template_snapshot_hash","read_only":1},
    {"fieldname":"qorg_terms_modified_after_copy","label":"Terms Modified After Template Copy","fieldtype":"Check","insert_after":"qorg_template_copied_on","read_only":1},
]

TEMPLATE_FIELDS = [
    {"fieldname":"qorg_governance_section","label":"QOrg Template Governance","fieldtype":"Section Break","insert_after":"title"},
    {"fieldname":"qorg_contract_type","label":"Contract Type","fieldtype":"Link","options":"QOrg Contract Type","insert_after":"qorg_governance_section","in_standard_filter":1},
    {"fieldname":"qorg_language","label":"Language","fieldtype":"Select","options":"English\nArabic\nBilingual","default":"Bilingual","insert_after":"qorg_contract_type"},
    {"fieldname":"qorg_version","label":"Version","fieldtype":"Int","default":"1","insert_after":"qorg_language","reqd":1},
    {"fieldname":"qorg_is_active","label":"Active","fieldtype":"Check","default":"1","insert_after":"qorg_version"},
    {"fieldname":"qorg_effective_from","label":"Effective From","fieldtype":"Date","insert_after":"qorg_is_active"},
    {"fieldname":"qorg_effective_to","label":"Effective To","fieldtype":"Date","insert_after":"qorg_effective_from"},
    {"fieldname":"qorg_approval_column","fieldtype":"Column Break","insert_after":"qorg_effective_to"},
    {"fieldname":"qorg_legal_approval_status","label":"Legal Approval Status","fieldtype":"Select","options":"Draft\nUnder Review\nApproved\nRetired","default":"Draft","insert_after":"qorg_approval_column"},
    {"fieldname":"qorg_approved_by","label":"Approved By","fieldtype":"Link","options":"User","insert_after":"qorg_legal_approval_status","read_only":1},
    {"fieldname":"qorg_approved_on","label":"Approved On","fieldtype":"Datetime","insert_after":"qorg_approved_by","read_only":1},
    {"fieldname":"qorg_supersedes_template","label":"Supersedes Template","fieldtype":"Link","options":"Contract Template","insert_after":"qorg_approved_on"},
    {"fieldname":"qorg_allow_contract_edits","label":"Allow Contract-specific Term Edits","fieldtype":"Check","default":"1","insert_after":"qorg_supersedes_template"},
    {"fieldname":"qorg_changes_require_legal_review","label":"Changes Require Legal Review","fieldtype":"Check","default":"1","insert_after":"qorg_allow_contract_edits"},
]


def provision_unified_contracts():
    definitions = {}
    if frappe.db.exists("DocType", "Contract"):
        definitions["Contract"] = CONTRACT_FIELDS
    if frappe.db.exists("DocType", "Contract Template"):
        definitions["Contract Template"] = TEMPLATE_FIELDS
    if definitions:
        create_custom_fields_if_changed(definitions, update=True)
    configure_standard_contract_meta()
    provision_contract_permissions()
    from qorg.qorg.unified_contracts.refinement import provision_refinement_fields
    provision_refinement_fields()
    provision_contract_types()
    reconcile_contract_type_policies()



def configure_standard_contract_meta():
    """Allow the unified party resolver to accept either standard or extended parties."""
    if not frappe.db.exists("DocType", "Contract"):
        return
    from frappe.custom.doctype.property_setter.property_setter import make_property_setter
    for fieldname in ("party_type", "party_name"):
        current = frappe.db.get_value("DocField", {"parent":"Contract", "fieldname":fieldname}, "reqd")
        if current:
            make_property_setter("Contract", fieldname, "reqd", 0, "Check", validate_fields_for_doctype=False)


def provision_contract_permissions():
    """Add domain roles without removing ERPNext's standard Contract permissions."""
    if not frappe.db.exists("DocType", "Contract"):
        return
    from frappe.permissions import add_permission, update_permission_property
    matrix = {
        "System Manager": (1, 1, 1, 1, 1, 1),
        "HR Manager": (1, 1, 1, 1, 1, 1),
        "Procurement Manager": (1, 1, 1, 1, 1, 1),
        "Accounts Manager": (1, 0, 0, 0, 0, 0),
        "Projects Manager": (1, 1, 1, 0, 0, 0),
        "Volunteer Manager": (1, 1, 1, 0, 0, 0),
        "Auditor": (1, 0, 0, 0, 0, 0),
    }
    for role, values in matrix.items():
        name = frappe.db.get_value("Custom DocPerm", {"parent":"Contract", "role":role, "permlevel":0}, "name")
        if not name:
            add_permission("Contract", role, 0)
        for prop, value in zip(("read","write","create","submit","cancel","amend"), values):
            update_permission_property("Contract", role, 0, prop, value)

def provision_contract_types():
    if not frappe.db.exists("DocType", "QOrg Contract Type"):
        return
    rows = [
        ("Employment Contract","Employment","Employee",1,0,0,1,0),
        ("Goods Supply Contract","Supply","Supplier",1,1,1,0,1),
        ("Service Contract","Service","Supplier",1,1,0,0,1),
        ("Works Contract","Works","Supplier",1,1,1,0,1),
        ("Consultancy Contract","Consultancy","Supplier\nEmployee",1,1,0,0,1),
        ("Volunteer Agreement","Volunteer","",0,0,0,0,0),
        ("Internship Agreement","Internship","",0,0,0,0,0),
        ("Customer Contract","Customer","Customer",1,0,0,0,0),
        ("Framework Agreement","Framework Agreement","Supplier",1,1,1,0,1),
        ("Funding Agreement","Funding / Grant","Customer",1,1,1,0,0),
        ("Partnership Agreement","Partnership","",0,1,1,0,0),
        ("Memorandum of Understanding","Memorandum of Understanding","",0,0,0,0,0),
    ]
    for name, category, party_types, value, funding, milestones, payroll, procurement in rows:
        if frappe.db.exists("QOrg Contract Type", name):
            continue
        doc = frappe.get_doc({"doctype":"QOrg Contract Type","type_name":name,"category":category,"allowed_party_types":party_types,"default_party_type":party_types.split("\n")[0] if party_types in {"Customer","Supplier","Employee"} else "","requires_value":value,"requires_funding_context":funding,"requires_milestones":milestones,"requires_payroll_activation":payroll,"requires_procurement_source":procurement,"is_active":1})
        doc.flags.ignore_validate = True
        doc.insert(ignore_permissions=True)



def reconcile_contract_type_policies():
    """Backfill the structured party policy without overwriting configured rows."""
    if not frappe.db.exists("DocType", "QOrg Contract Allowed Party"):
        return
    defaults = {
        "Employment Contract": ("Standard Party", [("Standard","Employee")]),
        "Goods Supply Contract": ("Standard Party", [("Standard","Supplier")]),
        "Service Contract": ("Standard Party", [("Standard","Supplier")]),
        "Works Contract": ("Standard Party", [("Standard","Supplier")]),
        "Consultancy Contract": ("Either Standard or Extended", [("Standard","Supplier"),("Standard","Employee"),("Extended","External Person")]),
        "Volunteer Agreement": ("Extended Party", [("Extended","External Person")]),
        "Internship Agreement": ("Extended Party", [("Extended","External Person")]),
        "Customer Contract": ("Standard Party", [("Standard","Customer")]),
        "Framework Agreement": ("Standard Party", [("Standard","Supplier")]),
        "Funding Agreement": ("Either Standard or Extended", [("Standard","Customer")]),
        "Partnership Agreement": ("Multiple Parties", [("Extended","Project Partner")]),
        "Memorandum of Understanding": ("Either Standard or Extended", [("Extended","Partner")]),
    }
    for name, (model, rows) in defaults.items():
        if not frappe.db.exists("QOrg Contract Type", name):
            continue
        doc = frappe.get_doc("QOrg Contract Type", name)
        changed = False
        if not doc.allowed_parties and doc.party_model != model:
            doc.party_model = model; changed = True
        if doc.requires_value and doc.allows_zero_value:
            doc.allows_zero_value = 0; changed = True
        if model == "Multiple Parties" and not doc.allow_multiple_parties:
            doc.allow_multiple_parties = 1; changed = True
        if not doc.allowed_parties:
            for idx, (mode, doctype) in enumerate(rows):
                if frappe.db.exists("DocType", doctype):
                    doc.append("allowed_parties", {"party_mode":mode,"party_doctype":doctype,"is_default":1 if idx == 0 else 0,"is_active":1})
                    changed = True
        if changed:
            doc.flags.ignore_validate = True
            doc.save(ignore_permissions=True)
