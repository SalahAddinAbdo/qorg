import frappe
from qorg.qorg.enterprise_foundation.idempotent_provisioning import create_custom_fields_if_changed
ROLES=['Procurement Officer','Procurement Manager','Bid Opening Committee Member','Technical Evaluation Committee Member','Financial Evaluation Committee Member','Main Committee Member','Procurement Award Approver','Budget Controller','Contract Manager']
METHODS=[('Direct Purchase','Direct',0,0,1),('Request for Quotations','RFQ',0,1,0),('Restricted Tender','Restricted',1,0,0),('Open Tender','Open',1,0,0),('Request for Proposals','RFP',1,0,0),('Single Source','Single Source',1,0,0),('Emergency Procurement','Emergency',1,0,0),('Framework Call-off','Framework',0,0,1)]
def provision_procurement_contracting():
 for role in ROLES:
  if not frappe.db.exists('Role',role): frappe.get_doc({'doctype':'Role','role_name':role,'desk_access':1}).insert(ignore_permissions=True)
 create_custom_fields_if_changed({'Material Request': [{'fieldname': 'qorg_procurement_section',
                        'label': 'Procurement Policy',
                        'fieldtype': 'Section Break',
                        'insert_after': 'schedule_date'},
                       {'fieldname': 'custom_procurement_type',
                        'label': 'Procurement Type',
                        'fieldtype': 'Select',
                        'options': 'Goods\nServices\nWorks\nConsultancy\nMixed',
                        'insert_after': 'qorg_procurement_section'},
                       {'fieldname': 'custom_estimated_procurement_value',
                        'label': 'Estimated Procurement Value',
                        'fieldtype': 'Currency',
                        'read_only': 1,
                        'insert_after': 'custom_procurement_type'},
                       {'fieldname': 'custom_procurement_policy_rule',
                        'label': 'Procurement Policy Rule',
                        'fieldtype': 'Link',
                        'options': 'Procurement Policy Rule',
                        'read_only': 1,
                        'insert_after': 'custom_estimated_procurement_value'},
                       {'fieldname': 'custom_procurement_method',
                        'label': 'Procurement Method',
                        'fieldtype': 'Link',
                        'options': 'Procurement Method',
                        'read_only': 1,
                        'insert_after': 'custom_procurement_policy_rule'},
                       {'fieldname': 'qorg_procurement_policy_column_2',
                        'label': '',
                        'fieldtype': 'Column Break',
                        'insert_after': 'custom_procurement_method'},
                       {'fieldname': 'custom_procurement_next_action',
                        'label': 'Next Procurement Action',
                        'fieldtype': 'Data',
                        'read_only': 1,
                        'insert_after': 'qorg_procurement_policy_column_2'},
                       {'fieldname': 'custom_requires_procurement_process',
                        'label': 'Requires Procurement Process',
                        'fieldtype': 'Check',
                        'read_only': 1,
                        'insert_after': 'custom_procurement_next_action'},
                       {'fieldname': 'custom_procurement_process',
                        'label': 'Procurement Process',
                        'fieldtype': 'Link',
                        'options': 'Procurement Process',
                        'read_only': 1,
                        'insert_after': 'custom_requires_procurement_process'},
                       {'fieldname': 'custom_minimum_quotations',
                        'label': 'Minimum Quotations',
                        'fieldtype': 'Int',
                        'read_only': 1,
                        'insert_after': 'custom_procurement_process'},
                       {'fieldname': 'qorg_procurement_requirements_section',
                        'label': 'Procurement Requirements',
                        'fieldtype': 'Section Break',
                        'insert_after': 'custom_minimum_quotations'},
                       {'fieldname': 'custom_requires_public_notice',
                        'label': 'Requires Public Notice',
                        'fieldtype': 'Check',
                        'read_only': 1,
                        'insert_after': 'qorg_procurement_requirements_section'},
                       {'fieldname': 'custom_requires_opening_committee',
                        'label': 'Requires Opening Committee',
                        'fieldtype': 'Check',
                        'read_only': 1,
                        'insert_after': 'custom_requires_public_notice'},
                       {'fieldname': 'custom_requires_technical_evaluation',
                        'label': 'Requires Technical Evaluation',
                        'fieldtype': 'Check',
                        'read_only': 1,
                        'insert_after': 'custom_requires_opening_committee'},
                       {'fieldname': 'qorg_procurement_requirements_column_2',
                        'label': '',
                        'fieldtype': 'Column Break',
                        'insert_after': 'custom_requires_technical_evaluation'},
                       {'fieldname': 'custom_requires_financial_evaluation',
                        'label': 'Requires Financial Evaluation',
                        'fieldtype': 'Check',
                        'read_only': 1,
                        'insert_after': 'qorg_procurement_requirements_column_2'},
                       {'fieldname': 'custom_requires_two_envelope',
                        'label': 'Requires Two Envelope',
                        'fieldtype': 'Check',
                        'read_only': 1,
                        'insert_after': 'custom_requires_financial_evaluation'},
                       {'fieldname': 'custom_requires_contract',
                        'label': 'Requires Contract',
                        'fieldtype': 'Check',
                        'read_only': 1,
                        'insert_after': 'custom_requires_two_envelope'},
                       {'fieldname': 'qorg_procurement_requirements_column_3',
                        'label': '',
                        'fieldtype': 'Column Break',
                        'insert_after': 'custom_requires_contract'},
                       {'fieldname': 'custom_technical_weight',
                        'label': 'Technical Weight %',
                        'fieldtype': 'Percent',
                        'read_only': 1,
                        'insert_after': 'qorg_procurement_requirements_column_3'},
                       {'fieldname': 'custom_financial_weight',
                        'label': 'Financial Weight %',
                        'fieldtype': 'Percent',
                        'read_only': 1,
                        'insert_after': 'custom_technical_weight'},
                       {'fieldname': 'custom_technical_threshold',
                        'label': 'Technical Threshold %',
                        'fieldtype': 'Percent',
                        'read_only': 1,
                        'insert_after': 'custom_financial_weight'},
                       {'fieldname': 'qorg_procurement_exception_section',
                        'label': 'Procurement Exception',
                        'fieldtype': 'Section Break',
                        'insert_after': 'custom_technical_threshold'},
                       {'fieldname': 'custom_procurement_exception_reason',
                        'label': 'Procurement Exception Reason',
                        'fieldtype': 'Small Text',
                        'insert_after': 'qorg_procurement_exception_section'},
                       {'fieldname': 'custom_procurement_policy_snapshot',
                        'label': 'Procurement Policy Snapshot',
                        'fieldtype': 'Long Text',
                        'read_only': 1,
                        'hidden': 1,
                        'insert_after': 'custom_procurement_exception_reason'}],
  'Purchase Order': [{'fieldname': 'custom_procurement_contract',
                      'label': 'Procurement Contract',
                      'fieldtype': 'Link',
                      'options': 'Procurement Contract',
                      'insert_after': 'project',
                      'read_only': 1,
                      'no_copy': 1},
                     {'fieldname': 'custom_procurement_process',
                      'label': 'Procurement Process',
                      'fieldtype': 'Link',
                      'options': 'Procurement Process',
                      'insert_after': 'custom_procurement_contract',
                      'read_only': 1,
                      'no_copy': 1}],
  'Purchase Receipt': [{'fieldname': 'custom_procurement_contract',
                        'label': 'Procurement Contract',
                        'fieldtype': 'Link',
                        'options': 'Procurement Contract',
                        'insert_after': 'project',
                        'read_only': 1,
                        'no_copy': 1}],
  'Purchase Invoice': [{'fieldname': 'custom_procurement_contract',
                        'label': 'Procurement Contract',
                        'fieldtype': 'Link',
                        'options': 'Procurement Contract',
                        'insert_after': 'project',
                        'read_only': 1,
                        'no_copy': 1}],
  'Material Request Item': [{'fieldname': 'qorg_estimate_section',
                             'label': 'Procurement Estimate',
                             'fieldtype': 'Section Break',
                             'insert_after': 'rate'},
                            {'fieldname': 'custom_estimated_unit_cost',
                             'label': 'Estimated Unit Cost',
                             'fieldtype': 'Currency',
                             'insert_after': 'qorg_estimate_section'},
                            {'fieldname': 'custom_estimated_amount',
                             'label': 'Estimated Amount',
                             'fieldtype': 'Currency',
                             'read_only': 1,
                             'insert_after': 'custom_estimated_unit_cost'},
                            {'fieldname': 'qorg_estimate_column_2',
                             'label': '',
                             'fieldtype': 'Column Break',
                             'insert_after': 'custom_estimated_amount'},
                            {'fieldname': 'custom_estimate_currency',
                             'label': 'Estimate Currency',
                             'fieldtype': 'Link',
                             'options': 'Currency',
                             'insert_after': 'qorg_estimate_column_2'},
                            {'fieldname': 'custom_estimate_source',
                             'label': 'Estimate Source',
                             'fieldtype': 'Select',
                             'options': 'Market Survey\n'
                                        'Previous Purchase\n'
                                        'Supplier Budgetary Quote\n'
                                        'Framework Agreement\n'
                                        'Catalogue\n'
                                        'Professional Estimate\n'
                                        'Other',
                             'insert_after': 'custom_estimate_currency'},
                            {'fieldname': 'qorg_estimate_column_3',
                             'label': '',
                             'fieldtype': 'Column Break',
                             'insert_after': 'custom_estimate_source'},
                            {'fieldname': 'custom_estimate_reference',
                             'label': 'Estimate Reference',
                             'fieldtype': 'Data',
                             'insert_after': 'qorg_estimate_column_3'},
                            {'fieldname': 'custom_non_stock_procurement_type',
                             'label': 'Non-stock Procurement Type',
                             'fieldtype': 'Select',
                             'options': 'Goods\nServices\nWorks\nConsultancy',
                             'insert_after': 'custom_estimate_reference'},
                            {'fieldname': 'qorg_specification_section',
                             'label': 'Required Specification or Scope',
                             'fieldtype': 'Section Break',
                             'insert_after': 'custom_non_stock_procurement_type'},
                            {'fieldname': 'custom_required_specification',
                             'label': 'Required Specification or Scope',
                             'fieldtype': 'Small Text',
                             'insert_after': 'qorg_specification_section'},
                            {'fieldname': 'qorg_delivery_section',
                             'label': 'Required Delivery',
                             'fieldtype': 'Section Break',
                             'insert_after': 'custom_required_specification'},
                            {'fieldname': 'custom_required_delivery_location',
                             'label': 'Required Delivery Location',
                             'fieldtype': 'Data',
                             'insert_after': 'qorg_delivery_section'},
                            {'fieldname': 'qorg_delivery_column_2',
                             'label': '',
                             'fieldtype': 'Column Break',
                             'insert_after': 'custom_required_delivery_location'},
                            {'fieldname': 'custom_required_delivery_date',
                             'label': 'Required Delivery Date',
                             'fieldtype': 'Date',
                             'insert_after': 'qorg_delivery_column_2'}]}, update=True)
 for name,mode,process,rfq,direct in METHODS:
  if not frappe.db.exists('Procurement Method',{'method_name':name}): frappe.get_doc({'doctype':'Procurement Method','naming_series':'PRM-.YYYY.-.#####','method_name':name,'procurement_mode':mode,'requires_procurement_process':process,'uses_standard_rfq':rfq,'allows_direct_purchase_order':direct}).insert(ignore_permissions=True)

WORKFLOW_STATES=["Draft Setup","Setup Approved","Published or Invited","Submission Closed","Opening Completed","Technical Evaluation In Progress","Technical Evaluation Approved","Financial Evaluation In Progress","Financial Evaluation Approved","Combined Evaluation Completed","Recommendation Submitted","Award Approved","Closed"]
def _provision_workflow_states():
 for state in WORKFLOW_STATES:
  if not frappe.db.exists("Workflow State",state): frappe.get_doc({"doctype":"Workflow State","workflow_state_name":state,"style":"Primary"}).insert(ignore_permissions=True)

def provision_procurement_contracting_full():
 provision_procurement_contracting(); _provision_workflow_states()

def _provision_budget_line_dimension():
 if not frappe.db.exists("DocType","Accounting Dimension") or not frappe.db.exists("DocType","Budget Line"): return
 meta=frappe.get_meta("Accounting Dimension")
 reference_field=next((f.fieldname for f in meta.fields if f.fieldname in ("document_type","reference_document_type")),None)
 if not reference_field: return
 if frappe.db.exists("Accounting Dimension",{reference_field:"Budget Line"}): return
 values={"doctype":"Accounting Dimension",reference_field:"Budget Line"}
 for field,value in (("label","Budget Line"),("fieldname","budget_line"),("disabled",0)):
  if meta.has_field(field): values[field]=value
 frappe.get_doc(values).insert(ignore_permissions=True)

def provision_procurement_contracting_full():
 provision_procurement_contracting(); _provision_workflow_states(); _provision_budget_line_dimension()

def provision_procurement_contracting_v13():
    provision_procurement_contracting_full()
    from qorg.qorg.procurement_contracting.notifications import provision_email_templates
    provision_email_templates()
def provision_procurement_contracting_v13_final():
    provision_procurement_contracting_v13()
    from qorg.qorg.procurement_contracting.settings import provision_buying_settings_extension
    from qorg.qorg.procurement_contracting.notifications import provision_notifications
    from qorg.qorg.procurement_contracting.workflows import provision_workflows
    from qorg.qorg.procurement_contracting.print_formats import provision_print_formats
    from qorg.qorg.procurement_contracting.web_forms import provision_procurement_web_forms
    provision_buying_settings_extension()
    provision_notifications()
    provision_workflows()
    provision_print_formats()
    provision_procurement_web_forms()

# Request for Quotation extensions. Kept in procurement_contracting to avoid a parallel module.
def _rfq_field(fieldname, label, fieldtype="Data", options=None, **kwargs):
    field = {"fieldname": fieldname, "label": label, "fieldtype": fieldtype, "module": "QOrg", "is_system_generated": 1}
    if options:
        field["options"] = options
    field.update(kwargs)
    return field


def provision_request_for_quotation_extensions():
    fields = {"Request for Quotation": [
        _rfq_field("qorg_quotation_section", "Quotation Contact and Submission", "Section Break", insert_after="schedule_date"),
        _rfq_field("custom_procurement_process", "Procurement Process", "Link", "Procurement Process", insert_after="qorg_quotation_section", read_only=1, in_standard_filter=1),
        _rfq_field("custom_contact_employee", "Contact Employee", "Link", "Employee", insert_after="custom_procurement_process"),
        _rfq_field("custom_contact_name", "Contact Name", insert_after="custom_contact_employee", read_only=1),
        _rfq_field("custom_contact_designation", "Contact Designation", insert_after="custom_contact_name", read_only=1),
        _rfq_field("qorg_contact_column", "", "Column Break", insert_after="custom_contact_designation"),
        _rfq_field("custom_contact_phone", "Contact Phone", "Data", "Phone", insert_after="qorg_contact_column"),
        _rfq_field("custom_contact_email", "Contact Email", "Data", "Email", insert_after="custom_contact_phone"),
        _rfq_field("custom_submission_deadline", "Submission Deadline", "Datetime", insert_after="custom_contact_email"),
        _rfq_field("custom_submission_method", "Submission Method", "Select", "Supplier Portal\nEmail\nSealed Envelope\nTwo Envelope\nOther", insert_after="custom_submission_deadline"),
        _rfq_field("custom_submission_location", "Submission Location", "Small Text", insert_after="custom_submission_method", depends_on='eval:["Sealed Envelope","Two Envelope","Other"].includes(doc.custom_submission_method)'),
        _rfq_field("custom_submission_instructions", "Submission Instructions", "Text Editor", insert_after="custom_submission_location"),
        _rfq_field("qorg_delivery_section", "Delivery and Commercial Terms", "Section Break", insert_after="custom_submission_instructions"),
        _rfq_field("custom_delivery_location", "Delivery Location", "Small Text", insert_after="qorg_delivery_section", mandatory_depends_on="eval:doc.docstatus == 1"),
        _rfq_field("qorg_terms_column", "", "Column Break", insert_after="custom_delivery_location"),
        _rfq_field("custom_offer_validity_days", "Offer Validity Days", "Int", insert_after="qorg_terms_column", default="30", non_negative=1),
        _rfq_field("custom_payment_terms", "Payment Terms", "Small Text", insert_after="custom_offer_validity_days"),
        _rfq_field("custom_prices_include_tax", "Prices Include Taxes", "Check", insert_after="custom_payment_terms"),
        _rfq_field("custom_prices_include_delivery", "Prices Include Delivery", "Check", insert_after="custom_prices_include_tax"),
        _rfq_field("qorg_requirements_section", "Security, Visit and Documents", "Section Break", insert_after="custom_prices_include_delivery"),
        _rfq_field("custom_bid_security_required", "Bid Security Required", "Check", insert_after="qorg_requirements_section"),
        _rfq_field("custom_bid_security_amount", "Bid Security Amount", "Currency", insert_after="custom_bid_security_required", depends_on="eval:doc.custom_bid_security_required == 1", mandatory_depends_on="eval:doc.custom_bid_security_required == 1"),
        _rfq_field("custom_bid_security_validity", "Bid Security Validity Days", "Int", insert_after="custom_bid_security_amount", depends_on="eval:doc.custom_bid_security_required == 1", mandatory_depends_on="eval:doc.custom_bid_security_required == 1", non_negative=1),
        _rfq_field("qorg_visit_column", "", "Column Break", insert_after="custom_bid_security_validity"),
        _rfq_field("custom_site_visit_required", "Site Visit Required", "Check", insert_after="qorg_visit_column"),
        _rfq_field("custom_site_visit_datetime", "Site Visit Date and Time", "Datetime", insert_after="custom_site_visit_required", depends_on="eval:doc.custom_site_visit_required == 1", mandatory_depends_on="eval:doc.custom_site_visit_required == 1"),
        _rfq_field("custom_site_visit_location", "Site Visit Location", "Small Text", insert_after="custom_site_visit_datetime", depends_on="eval:doc.custom_site_visit_required == 1", mandatory_depends_on="eval:doc.custom_site_visit_required == 1"),
        _rfq_field("custom_required_documents", "Required Documents", "Text Editor", insert_after="custom_site_visit_location"),
    ]}
    create_custom_fields_if_changed(fields, update=True)
    frappe.clear_cache(doctype="Request for Quotation")


# Wrap the existing final provisioner once so all procurement records converge together.
_provision_procurement_contracting_v13_final = provision_procurement_contracting_v13_final
def provision_procurement_contracting_v13_final():
    _provision_procurement_contracting_v13_final()
    provision_request_for_quotation_extensions()
    from qorg.qorg.procurement_contracting.communications import provision_email_templates
    from qorg.qorg.procurement_contracting.notifications import provision as provision_managed_notifications
    provision_email_templates()
    provision_managed_notifications()
