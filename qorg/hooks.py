"""QOrg hooks.

This module intentionally contains only the final declarative Frappe hook values.
Feature-specific registrations are grouped by hook type so the file is auditable
without changing runtime behavior or registration order.
"""

# ==============================================================================
# APPLICATION METADATA
# ==============================================================================

app_name = 'qorg'

app_title = 'QOrg'

app_publisher = 'QOrg'

app_description = 'Enterprise operations, programmes, finance, people, and governance for ERPNext'

app_email = ''

app_license = 'GPL-3.0'

app_logo_url = '/assets/qorg/images/qorg_project_cycle.png'

app_home = '/desk/q-management-hub'

add_to_apps_screen = [{'name': 'qorg',
  'logo': '/assets/qorg/images/qorg_project_cycle.png',
  'title': 'QOrg',
  'route': '/desk/q-management-hub',
  'sequence_id': 5}]

required_apps = ['erpnext', 'hrms']

# ==============================================================================
# BOOT AND FRAMEWORK EXTENSIONS
# ==============================================================================

extend_bootinfo = 'qorg.qorg.enterprise_foundation.boot.extend_bootinfo'

override_whitelisted_methods = {'frappe.model.rename_doc.update_document_title': 'qorg.qorg.enterprise_foundation.overrides.update_document_title'}

extend_doctype_class = {'Task': ['qorg.qorg.task_management.task_controller.TaskProjectPeriodPolicyMixin'],
 'Material Request': ['qorg.qorg.procurement_contracting.material_request.MaterialRequestProcurementMixin']}

override_doctype_dashboards = {'Material Request': 'qorg.qorg.dashboards.material_request.get_data',
 'Contract': 'qorg.qorg.dashboards.contract.get_data',
 'Employee Separation': 'qorg.qorg.employee_lifecycle.separation_clearance.dashboard.get_data'}

# ==============================================================================
# DESK ASSETS
# ==============================================================================

app_include_js = [
    '/assets/qorg/js/cost_distribution.js','/assets/qorg/js/finance_budget_grants.js',
 '/assets/qorg/js/shared_cost_reports.js',
 '/assets/qorg/js/document_workflow.js',
 '/assets/qorg/js/qorg_form_bootstrap.js',
 '/assets/qorg/js/model_policy.js',
 '/assets/qorg/js/qorg_action_rail.js',
 '/assets/qorg/js/qorg_language_action.js',
 '/assets/qorg/js/qorg_quick_create_action.js',
 '/assets/qorg/js/qorg_open_action.js',
 '/assets/qorg/js/qorg_ui_tokens.js',
 '/assets/qorg/js/qorg_theme_runtime.js',
 '/assets/qorg/js/procurement_reports.js',
 '/assets/qorg/js/procurement_communications.js',
 '/assets/qorg/js/inventory_cycle.js']

app_include_css = ['/assets/qorg/css/model_policy.css',
 '/assets/qorg/css/qorg_action_rail.css',
 '/assets/qorg/css/qorg_ui_tokens.css',
 '/assets/qorg/css/qorg_theme_runtime.css',
 '/assets/qorg/css/qorg_desk_controls.css',
 '/assets/qorg/css/procurement_reports.css']

# ==============================================================================
# WEBSITE ASSETS AND ROUTING
# ==============================================================================

web_include_css = ['/assets/qorg/css/qorg_ui_tokens.css',
 '/assets/qorg/css/qorg_theme_runtime.css',
 '/assets/qorg/css/qorg_portal.css',
 'qorg_login_experience.bundle.css',
 '/assets/qorg/css/qorg_login_experience_hotfix.css',
 '/assets/qorg/css/qorg_field_controls.css',
 '/assets/qorg/css/procurement_portal.css']

web_include_js = ['/assets/qorg/js/qorg_ui_tokens.js',
 '/assets/qorg/js/qorg_theme_runtime.js',
 'qorg_login_experience.bundle.js',
 '/assets/qorg/js/qorg_login_experience_hotfix.js',
 '/assets/qorg/js/qorg_supplier_portal_nav.js',
 '/assets/qorg/js/qorg_people_portal_nav.js',
 '/assets/qorg/js/qorg_web_select.js']

website_route_rules = [{'from_route': '/opportunities/<route>', 'to_route': 'opportunities/detail'},
 {'from_route': '/participation-application/list', 'to_route': 'my-applications'},
 {'from_route': '/tender-submission/list', 'to_route': 'my-bids'}]

website_redirects = [{'source': '/external-profile', 'target': '/external-profile-form'}]

standard_portal_menu_items = [{'title': 'Opportunities', 'route': '/opportunities', 'reference_doctype': 'External Opportunity'},
 {'title': 'My Applications',
  'route': '/my-applications',
  'reference_doctype': 'Participation Application',
  'role': 'External Applicant'},
 {'title': 'My Profile',
  'route': '/external-profile-form',
  'reference_doctype': 'External Person',
  'role': 'External Applicant'}]

# ==============================================================================
# DOCTYPE CLIENT SCRIPTS
# ==============================================================================

doctype_js = {'Website Settings': 'public/js/website_settings_opportunity_portal.js',
 'HR Settings': 'public/js/hr_settings_recruitment.js',
 'Designation': 'public/js/designation_recruitment.js',
 'Interview Type': 'public/js/interview_type.js',
 'Interview Feedback': ['public/js/interview_feedback.js',
                        'public/js/recruitment_communications.js'],
 'Job Applicant': ['public/js/job_applicant_recruitment.js',
                   'public/js/recruitment_communications.js'],
 'Task Assignment Request': 'public/js/task_assignment_request.js',
 'Task': 'public/js/task.js',
 'Employee': 'public/js/employee_announcement.js',
 'Contract': ['public/js/unified_contract.js'],
 'Contract Template': ['public/js/contract_template_qorg.js'],
 'QOrg Contract Type': ['public/js/qorg_contract_type.js'],
 'Notification': 'public/js/notification_configuration.js',
 'Workflow': 'public/js/workflow_engine.js',
 'Projects Settings': 'public/js/projects_settings.js',
 'Print Settings': 'public/js/print_settings.js',
 'Material Request': 'public/js/material_request_procurement.js',
 'Request for Quotation': 'public/js/request_for_quotation.js',
 'Interview': ['public/js/recruitment_communications.js'],
 'Job Offer': ['public/js/recruitment_communications.js'],
 'Appointment Letter': ['public/js/recruitment_communications.js'],
 'Employee Onboarding': ['public/js/recruitment_communications.js'],
 'Employee Boarding Activity': ['public/js/recruitment_communications.js'],
 'Work Commencement Notice': ['public/js/recruitment_communications.js'],
 'Participation Application': ['public/js/participation_communications.js'],
 'Participation Engagement': ['public/js/participation_communications.js'],
 'Participation Service Log': ['public/js/participation_communications.js'],
 'Participation Certificate': ['public/js/participation_communications.js'],
 'Procurement Complaint': ['public/js/procurement_complaint.js'],
 'Employee Separation': ['public/js/employee_separation_clearance.js'],
 'Employee Offboarding': ['public/js/employee_separation_clearance.js']}

# ==============================================================================
# DOCUMENT EVENTS
# ==============================================================================

doc_events = {'Web Form': {'before_validate': 'qorg.qorg.people_and_opportunities.web_form_policy.validate_web_form_policy'},
 'Designation': {'validate': ['qorg.qorg.recruitment_extensions.events.designation_validate',
                              'qorg.qorg.recruitment_extensions.validation.validate_designation']},
 'External Person': {'on_update': 'qorg.qorg.people_and_opportunities.portal_settings.sync_external_person_portal_access',
                     'on_trash': 'qorg.qorg.people_and_opportunities.integrity.prevent_operational_delete',
                     'validate': 'qorg.qorg.people_and_opportunities.cycle_integrity.validate_external_person_links'},
 'External Opportunity': {'validate': ['qorg.qorg.volunteer_management.events.validate_external_opportunity',
                                       'qorg.qorg.people_and_opportunities.portal.validate_external_opportunity_publication',
                                       'qorg.qorg.people_and_opportunities.cycle_integrity.validate_external_opportunity_links'],
                          'on_update': 'qorg.qorg.people_and_opportunities.portal.handle_external_opportunity_publication',
                          'on_trash': 'qorg.qorg.people_and_opportunities.integrity.prevent_operational_delete'},
 'Participation Application': {'on_trash': 'qorg.qorg.volunteer_management.integrity.prevent_operational_delete',
                               'validate': 'qorg.qorg.volunteer_management.cycle_integrity.validate_participation_record'},
 'Participation Assessment': {'on_trash': 'qorg.qorg.volunteer_management.integrity.prevent_operational_delete',
                              'validate': 'qorg.qorg.volunteer_management.cycle_integrity.validate_participation_record'},
 'Participation Engagement': {'on_trash': 'qorg.qorg.volunteer_management.integrity.prevent_operational_delete',
                              'validate': 'qorg.qorg.volunteer_management.cycle_integrity.validate_participation_record'},
 'Participation Service Log': {'on_trash': 'qorg.qorg.volunteer_management.integrity.prevent_operational_delete',
                               'validate': 'qorg.qorg.volunteer_management.cycle_integrity.validate_participation_record'},
 'Participation Evaluation': {'on_trash': 'qorg.qorg.volunteer_management.integrity.prevent_operational_delete',
                              'validate': 'qorg.qorg.volunteer_management.cycle_integrity.validate_participation_record'},
 'Participation Certificate': {'on_trash': 'qorg.qorg.volunteer_management.integrity.prevent_operational_delete',
                               'validate': 'qorg.qorg.volunteer_management.cycle_integrity.validate_participation_record'},
 'External Opportunity Type': {'on_trash': 'qorg.qorg.people_and_opportunities.integrity.prevent_master_delete'},
 'Person Qualification': {'on_trash': 'qorg.qorg.people_and_opportunities.integrity.prevent_master_delete'},
 'Volunteer Category': {'on_trash': 'qorg.qorg.people_and_opportunities.integrity.prevent_master_delete'},
 'Job Opening': {'validate': ['qorg.qorg.people_and_opportunities.integrations.validate_job_opening',
                              'qorg.qorg.recruitment_extensions.events.opening_validate',
                              'qorg.qorg.recruitment_extensions.defaults.apply_job_opening_defaults',
                              'qorg.qorg.recruitment_extensions.validation.validate_job_opening']},
 'Job Applicant': {'before_validate': ['qorg.qorg.people_and_opportunities.integrations.sync_job_applicant_person',
                                       'qorg.qorg.recruitment_extensions.defaults.validate_job_applicant_policy',
                                       'qorg.qorg.recruitment_extensions.events.applicant_validate'],
                   'on_update': 'qorg.qorg.people_and_opportunities.integrations.sync_job_applicant_person',
                   'validate': 'qorg.qorg.people_and_opportunities.cycle_integrity.validate_job_applicant_person'},
 'Interview Type': {'validate': ['qorg.qorg.recruitment_extensions.defaults.apply_interview_type_defaults',
                                 'qorg.qorg.recruitment_extensions.events.interview_type_validate',
                                 'qorg.qorg.recruitment_extensions.validation.validate_interview_type']},
 'Interview Feedback': {'before_validate': ['qorg.qorg.recruitment_extensions.events.feedback_validate',
                                            'qorg.qorg.recruitment_extensions.defaults.validate_feedback_policy',
                                            'qorg.qorg.recruitment_extensions.validation.validate_feedback'],
                        'on_submit': 'qorg.qorg.recruitment_extensions.events.feedback_submit',
                        'on_cancel': 'qorg.qorg.recruitment_extensions.events.feedback_cancel',
                        'after_delete': 'qorg.qorg.recruitment_extensions.events.feedback_delete'},
 'Interview': {'validate': ['qorg.qorg.recruitment_extensions.defaults.apply_interview_defaults',
                            'qorg.qorg.recruitment_extensions.events.interview_validate'],
               'on_cancel': 'qorg.qorg.recruitment_extensions.events.interview_cancel',
               'on_trash': 'qorg.qorg.recruitment_extensions.events.interview_trash'},
 'Job Offer': {'before_validate': ['qorg.qorg.recruitment_extensions.defaults.apply_job_offer_defaults',
                                   'qorg.qorg.recruitment_extensions.events.offer_before_validate'],
               'on_update': 'qorg.qorg.recruitment_extensions.events.offer_on_update'},
 'Appointment Letter': {'validate': 'qorg.qorg.recruitment_extensions.events.appointment_validate',
                        'on_update': 'qorg.qorg.recruitment_extensions.events.appointment_on_update'},
 'Employee': {'validate': 'qorg.qorg.recruitment_extensions.events.employee_validate',
              'after_insert': 'qorg.qorg.recruitment_extensions.events.employee_after_insert'},
 'Employee Onboarding': {'before_validate': 'qorg.qorg.recruitment_extensions.defaults.apply_onboarding_defaults',
                         'validate': ['qorg.qorg.recruitment_extensions.events.onboarding_validate',
                                      'qorg.qorg.recruitment_extensions.onboarding.validate_onboarding']},
 'Website Settings': {'validate': 'qorg.qorg.people_and_opportunities.portal_settings.validate_website_settings'},
 'HR Settings': {'validate': 'qorg.qorg.recruitment_extensions.settings.validate_hr_settings'},
 'Print Settings': {'validate': 'qorg.qorg.project_management.print_settings_integration.validate_print_settings'},
 'Project Risk': {'on_update': 'qorg.qorg.project_management.notification_engine.process_project_notification_on_update',
                  'validate': 'qorg.qorg.project_management.cycle_integrity.validate_project_cycle_links'},
 'Task': {'before_validate': 'qorg.qorg.task_management.events.before_validate',
          'on_update': 'qorg.qorg.task_management.events.on_update',
          'after_delete': 'qorg.qorg.task_management.events.after_delete'},
 'Workflow': {'validate': 'qorg.qorg.workflow.provisioning.validate_workflow_configuration',
              'on_update': 'qorg.qorg.workflow.provisioning.ensure_current_responsible_user'},
 '*': {'before_insert': 'qorg.qorg.enterprise_foundation.policy_enforcement.enforce_model_policy',
       'before_save': 'qorg.qorg.enterprise_foundation.policy_enforcement.enforce_model_policy',
       'before_submit': 'qorg.qorg.enterprise_foundation.policy_enforcement.enforce_model_policy',
       'before_cancel': 'qorg.qorg.enterprise_foundation.policy_enforcement.enforce_model_policy',
       'before_update_after_submit': 'qorg.qorg.enterprise_foundation.policy_enforcement.enforce_model_policy',
       'on_trash': 'qorg.qorg.enterprise_foundation.policy_enforcement.enforce_model_policy',
       'validate': 'qorg.qorg.workflow.permissions.validate_responsible_user'},
 'Purchase Invoice': {'validate': ['qorg.qorg.procurement_contracting.acceptance.validate_purchase_invoice',
                                   'qorg.qorg.procurement_contracting.standard_guards.validate_contract_links',
                                   'qorg.qorg.finance_budget_grants.services.validate_accounting_document'],
                      'on_submit': ['qorg.qorg.finance_period_control.routing_v2.purchase_invoice_submit'],
                      'on_cancel': ['qorg.qorg.finance_period_control.settlement_v2.cancel_source']},
 'Supplier Registration': {'validate': ['qorg.qorg.procurement_contracting.supplier_profile.validate_supplier_registration']},
 'Material Request': {'on_submit': ['qorg.qorg.procurement_contracting.routing.route_material_request',
                                    'qorg.qorg.finance_period_control.routing_v2.material_request_submit'],
                      'on_cancel': ['qorg.qorg.finance_period_control.settlement_v2.cancel_source'],
                      'validate': ['qorg.qorg.inventory_asset_custody.issue_control.validate_material_request_activity',
                                   'qorg.qorg.finance_budget_grants.services.validate_accounting_document']},
 'Framework Call Off': {'validate': ['qorg.qorg.procurement_contracting.contract_engine.validate_framework_call_off']},
 'Procurement Submission': {'validate': ['qorg.qorg.procurement_contracting.submission_service.validate_submission']},
 'Purchase Order': {'on_submit': ['qorg.qorg.finance_period_control.routing_v2.purchase_order_submit'],
                    'on_cancel': ['qorg.qorg.finance_period_control.settlement_v2.cancel_source'],
                    'validate': ['qorg.qorg.procurement_contracting.standard_guards.validate_purchase_order',
                                 'qorg.qorg.procurement_contracting.standard_guards.validate_contract_links',
                                 'qorg.qorg.finance_budget_grants.services.validate_accounting_document']},
 'Procure Acceptance': {'on_submit': ['qorg.qorg.procurement_contracting.commitment_hooks.acceptance_submit'],
                        'on_cancel': ['qorg.qorg.procurement_contracting.commitment_hooks.acceptance_cancel'],
                        'validate': ['qorg.qorg.procurement_contracting.contract_engine.validate_acceptance']},
 'Payment Entry': {'on_submit': ['qorg.qorg.finance_period_control.settlement_v2.payment_submit'],
                   'on_cancel': ['qorg.qorg.finance_period_control.settlement_v2.cancel_source'],
                   'validate': 'qorg.qorg.finance_budget_grants.services.validate_accounting_document'},
 'Buying Settings': {'validate': ['qorg.qorg.procurement_contracting.settings.validate_buying_settings']},
 'Request for Quotation': {'validate': ['qorg.qorg.procurement_contracting.standard_guards.validate_rfq']},
 'Purchase Receipt': {'validate': ['qorg.qorg.procurement_contracting.standard_guards.validate_contract_links',
                                   'qorg.qorg.inventory_asset_custody.receipt_control.reconcile_receipt',
                                   'qorg.qorg.inventory_asset_custody.inspection_control.validate_generated_return_receipt',
                                   'qorg.qorg.finance_budget_grants.services.validate_accounting_document'],
                      'on_submit': ['qorg.qorg.inventory_asset_custody.inspection_control.register_return_purchase_receipt'],
                      'on_cancel': ['qorg.qorg.inventory_asset_custody.inspection_control.unregister_return_purchase_receipt']},
 'Procurement Process': {'on_update': ['qorg.qorg.procurement_contracting.event_handlers.notify_assigned_committee']},
 'Quality Inspection': {'validate': ['qorg.qorg.inventory_asset_custody.inspection_control.validate_inspection']},
 'Stock Entry': {'validate': ['qorg.qorg.inventory_asset_custody.warehouse_policy.validate_stock_entry',
                              'qorg.qorg.inventory_asset_custody.issue_control.validate_stock_entry',
                              'qorg.qorg.inventory_asset_custody.inspection_control.validate_generated_stock_entry',
                              'qorg.qorg.finance_budget_grants.services.validate_accounting_document'],
                 'on_submit': ['qorg.qorg.inventory_asset_custody.issue_control.update_material_request',
                               'qorg.qorg.inventory_asset_custody.inspection_control.register_release_stock_entry'],
                 'on_cancel': ['qorg.qorg.inventory_asset_custody.issue_control.update_material_request',
                               'qorg.qorg.inventory_asset_custody.inspection_control.unregister_release_stock_entry']},
 'Asset': {'validate': ['qorg.qorg.inventory_asset_custody.asset_control.validate_asset',
                        'qorg.qorg.finance_budget_grants.services.validate_accounting_document']},
 'Asset Movement': {'validate': ['qorg.qorg.inventory_asset_custody.asset_control.validate_movement']},
 'Employee Separation': {'validate': ['qorg.qorg.inventory_asset_custody.asset_control.prevent_separation',
                                      'qorg.qorg.recruitment_extensions.employee_cycle_integrity.prevent_incomplete_employee_exit',
                                      'qorg.qorg.employee_lifecycle.separation_clearance.services.validate_employee_clearance']},
 'Employee Offboarding': {'validate': ['qorg.qorg.inventory_asset_custody.asset_control.prevent_separation',
                                       'qorg.qorg.recruitment_extensions.employee_cycle_integrity.prevent_incomplete_employee_exit',
                                       'qorg.qorg.employee_lifecycle.separation_clearance.services.validate_employee_clearance']},
 'Project Result': {'validate': 'qorg.qorg.project_management.cycle_integrity.validate_project_cycle_links'},
 'Project Indicator': {'validate': 'qorg.qorg.project_management.cycle_integrity.validate_project_cycle_links'},
 'Indicator Target Plan': {'validate': 'qorg.qorg.project_management.cycle_integrity.validate_project_cycle_links'},
 'Project Workplan Activity': {'validate': 'qorg.qorg.project_management.cycle_integrity.validate_project_cycle_links'},
 'Project Progress Update': {'validate': 'qorg.qorg.project_management.cycle_integrity.validate_project_cycle_links'},
 'Project Change Request': {'validate': ['qorg.qorg.project_management.cycle_integrity.validate_project_cycle_links',
                                         'qorg.qorg.finance_budget_grants.budget_transfers.validate_budget_transfer'],
                            'on_update': 'qorg.qorg.finance_budget_grants.budget_transfers.apply_approved_budget_transfer',
                            'on_cancel': 'qorg.qorg.finance_budget_grants.budget_transfers.reverse_budget_transfer'},
 'Project Compliance Deliverable': {'validate': 'qorg.qorg.project_management.cycle_integrity.validate_project_cycle_links'},
 'Project Beneficiary Plan': {'validate': 'qorg.qorg.project_management.cycle_integrity.validate_project_cycle_links'},
 'Project Closure': {'validate': ['qorg.qorg.project_management.cycle_integrity.validate_project_cycle_links',
                                  'qorg.qorg.finance_budget_grants.closeout.validate_project_closeout'],
                     'before_validate': 'qorg.qorg.finance_budget_grants.closeout.refresh_project_closeout'},
 'Work Commencement Notice': {'validate': 'qorg.qorg.recruitment_extensions.employee_cycle_integrity.validate_work_commencement'},
 'Journal Entry': {'validate': 'qorg.qorg.finance_budget_grants.services.validate_accounting_document'},
 'Expense Claim': {'validate': 'qorg.qorg.finance_budget_grants.services.validate_accounting_document'},
 'Payroll Entry': {'validate': 'qorg.qorg.finance_budget_grants.services.validate_accounting_document'},
 'Salary Slip': {'validate': 'qorg.qorg.finance_budget_grants.services.validate_accounting_document'},
 'Budget Line': {'before_validate': 'qorg.qorg.finance_budget_grants.services.apply_budget_line_defaults',
                 'validate': 'qorg.qorg.finance_budget_grants.services.validate_budget_line'},
 'Project': {'validate': 'qorg.qorg.finance_budget_grants.services.validate_project_funding_source'},
 'Funding Agreement': {'on_update': 'qorg.qorg.finance_budget_grants.budget_transfers.sync_funding_agreement_to_project'},
 'Contract': {'validate': ['qorg.qorg.unified_contracts.services.validate_contract',
                            'qorg.qorg.procurement_contracting.contract_engine.validate_contract'],
              'on_submit': 'qorg.qorg.procurement_contracting.commitment_hooks.contract_submit',
              'on_cancel': 'qorg.qorg.procurement_contracting.commitment_hooks.contract_cancel'},
 'Contract Template': {'validate': 'qorg.qorg.unified_contracts.services.validate_template'}}

# ==============================================================================
# PERMISSIONS
# ==============================================================================

permission_query_conditions = {'Contract': 'qorg.qorg.unified_contracts.permissions.contract_query_condition',
 'Task': 'qorg.qorg.task_management.permissions.task_query_condition',
 'Task Assignment Request': 'qorg.qorg.task_management.permissions.request_query_condition',
 'Technical Evaluation': 'qorg.qorg.procurement_contracting.permissions.technical_query',
 'Financial Evaluation': 'qorg.qorg.procurement_contracting.permissions.financial_query',
 'Project Result': 'qorg.qorg.project_management.permissions.project_result_query',
 'Project Indicator': 'qorg.qorg.project_management.permissions.project_indicator_query',
 'Indicator Target Plan': 'qorg.qorg.project_management.permissions.indicator_target_plan_query',
 'Project Workplan Activity': 'qorg.qorg.project_management.permissions.project_workplan_activity_query',
 'Project Progress Update': 'qorg.qorg.project_management.permissions.project_progress_update_query',
 'Project Risk': 'qorg.qorg.project_management.permissions.project_risk_query',
 'Project Change Request': 'qorg.qorg.project_management.permissions.project_change_request_query',
 'Project Compliance Deliverable': 'qorg.qorg.project_management.permissions.project_compliance_deliverable_query',
 'Project Beneficiary Plan': 'qorg.qorg.project_management.permissions.project_beneficiary_plan_query',
 'Project Closure': 'qorg.qorg.project_management.permissions.project_closure_query',
 'Procurement Complaint': 'qorg.qorg.procurement_contracting.complaint_permissions.query',
 'Funding Agreement': 'qorg.qorg.finance_budget_grants.permissions.funding_agreement_query',
 'Budget Transfer Audit': 'qorg.qorg.finance_budget_grants.permissions.budget_transfer_audit_query'}

has_permission = {'Contract': 'qorg.qorg.unified_contracts.permissions.contract_has_permission',
 'Feature Control Center': 'qorg.qorg.enterprise_foundation.permissions.feature_control_center_has_permission',
 'Managed Configuration State': 'qorg.qorg.enterprise_foundation.permissions.managed_state_has_permission',
 'Task': 'qorg.qorg.task_management.permissions.has_task_permission',
 'Task Assignment Request': 'qorg.qorg.task_management.permissions.has_request_permission',
 'Procurement Submission': 'qorg.qorg.procurement_contracting.permissions.submission_has_permission',
 'Financial Evaluation': 'qorg.qorg.procurement_contracting.permissions.financial_evaluation_has_permission',
 'Technical Evaluation': 'qorg.qorg.procurement_contracting.permissions.technical_evaluation_has_permission',
 'Project Result': 'qorg.qorg.project_management.permissions.project_result_has',
 'Project Indicator': 'qorg.qorg.project_management.permissions.project_indicator_has',
 'Indicator Target Plan': 'qorg.qorg.project_management.permissions.indicator_target_plan_has',
 'Project Workplan Activity': 'qorg.qorg.project_management.permissions.project_workplan_activity_has',
 'Project Progress Update': 'qorg.qorg.project_management.permissions.project_progress_update_has',
 'Project Risk': 'qorg.qorg.project_management.permissions.project_risk_has',
 'Project Change Request': 'qorg.qorg.project_management.permissions.project_change_request_has',
 'Project Compliance Deliverable': 'qorg.qorg.project_management.permissions.project_compliance_deliverable_has',
 'Project Beneficiary Plan': 'qorg.qorg.project_management.permissions.project_beneficiary_plan_has',
 'Project Closure': 'qorg.qorg.project_management.permissions.project_closure_has',
 'Procurement Complaint': 'qorg.qorg.procurement_contracting.complaint_permissions.has',
 'Funding Agreement': 'qorg.qorg.finance_budget_grants.permissions.funding_agreement_permission',
 'Budget Transfer Audit': 'qorg.qorg.finance_budget_grants.permissions.budget_transfer_audit_permission'}

file_permission = ['qorg.qorg.procurement_contracting.private_files.has_file_permission']

# ==============================================================================
# SCHEDULER
# ==============================================================================

scheduler_events = {'daily': ['qorg.qorg.unified_contracts.services.update_expiring_contracts',
'qorg.qorg.recruitment_extensions.settings_jobs.run_daily_recruitment_settings_jobs',
           'qorg.qorg.people_and_opportunities.portal_scheduler.close_expired_public_opportunities',
           'qorg.qorg.project_management.notification_engine.run_daily_project_notifications',
           'qorg.qorg.project_management.integrity_jobs.run_daily_project_reconciliation',
           'qorg.qorg.procurement_contracting.scheduled_tasks.daily_procurement_alerts',
           'qorg.qorg.procurement_contracting.scheduled_tasks.send_procurement_reminders',
           'qorg.qorg.inventory_asset_custody.scheduled_tasks.send_inventory_reminders',
           'qorg.qorg.finance_budget_grants.scheduled_tasks.send_funding_reminders'],
 'cron': {'*/15 * * * *': ['qorg.qorg.task_management.scheduler.run_scheduled_task_summary']}}

# ==============================================================================
# INSTALLATION AND MIGRATION
# ==============================================================================

before_migrate = ['qorg.qorg.project_management.identity_migration.prepare_q_org_identity',
 'qorg.qorg.project_management.workspace_migration.prepare_q_management_hub']

after_install = ['qorg.qorg.finance_budget_grants.provisioning.provision_finance_budget_grants',
 'qorg.qorg.workflow.provisioning.provision_workflow_responsibility_routing',
 'qorg.qorg.recruitment_extensions.settings_provisioning.provision_recruitment_settings',
 'qorg.qorg.recruitment_extensions.provisioning.provision_recruitment_extensions',
 'qorg.qorg.people_and_opportunities.provisioning.provision_people_opportunities_core',
 'qorg.qorg.people_and_opportunities.portal_provisioning.provision_opportunity_portal',
 'qorg.qorg.people_and_opportunities.web_form_provisioning.provision_standard_opportunity_web_forms',
 'qorg.qorg.people_and_opportunities.web_form_policy.reconcile_web_form_policy',
 'qorg.qorg.volunteer_management.provisioning.provision_volunteer_management',
 'qorg.qorg.project_management.print_settings_integration.provision_print_settings',
 'qorg.qorg.install.after_install',
 'qorg.qorg.task_management.provisioning.provision_task_integration',
 'qorg.qorg.project_management.provisioning.provision_project_management',
 'qorg.qorg.project_management.workflow_provisioning.provision_project_workflows',
 'qorg.qorg.project_management.notification_provisioning.provision_project_notifications',
 'qorg.qorg.enterprise_foundation.provisioning.provision_enterprise_foundation',
 'qorg.qorg.design_system.provisioning.provision_login_experience',
 'qorg.qorg.project_management.navigation_provisioning.provision_q_org_navigation',
 'qorg.qorg.procurement_contracting.provisioning.provision_procurement_contracting_v13_final',
 'qorg.qorg.inventory_asset_custody.custom_fields.provision_custom_fields',
 'qorg.qorg.inventory_asset_custody.communications.provision_communications',
 'qorg.qorg.inventory_asset_custody.workflows.provision_workflows',
 'qorg.qorg.inventory_asset_custody.print_formats.provision_print_formats']

after_migrate = ['qorg.qorg.unified_contracts.provisioning.provision_unified_contracts',
 'qorg.qorg.finance_budget_grants.provisioning.provision_finance_budget_grants',
 'qorg.qorg.workflow.provisioning.provision_workflow_responsibility_routing',
 'qorg.qorg.recruitment_extensions.settings_provisioning.provision_recruitment_settings',
 'qorg.qorg.recruitment_extensions.provisioning.provision_recruitment_extensions',
 'qorg.qorg.people_and_opportunities.provisioning.provision_people_opportunities_core',
 'qorg.qorg.people_and_opportunities.portal_provisioning.provision_opportunity_portal',
 'qorg.qorg.people_and_opportunities.web_form_provisioning.provision_standard_opportunity_web_forms',
 'qorg.qorg.people_and_opportunities.web_form_policy.reconcile_web_form_policy',
 'qorg.qorg.doctype.participation_application.participation_application.reconcile_all_opportunity_application_stats',
 'qorg.qorg.volunteer_management.provisioning.provision_volunteer_management',
 'qorg.qorg.project_management.print_settings_integration.provision_print_settings',
 'qorg.qorg.install.after_migrate',
 'qorg.printing.provisioning.provision_universal_print_formats',
 'qorg.qorg.project_management.print_settings_cleanup.remove_legacy_print_settings',
 'qorg.qorg.task_management.provisioning.provision_task_integration',
 'qorg.qorg.project_management.provisioning.provision_project_management',
 'qorg.qorg.project_management.workflow_provisioning.provision_project_workflows',
 'qorg.qorg.project_management.notification_provisioning.provision_project_notifications',
 'qorg.qorg.enterprise_foundation.provisioning.provision_enterprise_foundation',
 'qorg.qorg.design_system.migration.migrate_login_experience',
 'qorg.qorg.design_system.provisioning.provision_login_experience',
 'qorg.qorg.project_management.navigation_provisioning.provision_q_org_navigation',
 'qorg.qorg.procurement_contracting.provisioning.provision_procurement_contracting_v13_final',
 'qorg.qorg.inventory_asset_custody.custom_fields.provision_custom_fields',
 'qorg.qorg.inventory_asset_custody.communications.provision_communications',
 'qorg.qorg.inventory_asset_custody.workflows.provision_workflows',
 'qorg.qorg.inventory_asset_custody.print_formats.provision_print_formats',
 'qorg.qorg.finance_budget_grants.migration.migrate_finance_budget_grants_v153',
 'qorg.qorg.finance_budget_grants.migration.migrate_finance_budget_grants_v154',
 'qorg.qorg.finance_budget_grants.migration.migrate_finance_budget_grants_v155',
 'qorg.qorg.finance_budget_grants.migration.migrate_finance_budget_grants_v156',
 'qorg.qorg.printing.page_break_provisioning.provision_printable_child_row_page_breaks',
 'qorg.qorg.printing.email_template_hardening.harden_email_template_previews']

# ==============================================================================
# FIXTURES
# ==============================================================================

fixtures = [{'dt': 'Custom Field',
  'filters': [['name',
               'in',
               ['Workflow Transition-custom_employee_signature_mapping_key',
                'Workflow Transition-custom_apply_employee_signature',
                'Workflow Transition-custom_notify_document_creator',
                'Workflow Transition-custom_column_break_6mqhf',
                'Workflow Transition-custom_section_break_h8b1r',
                'Workflow Transition-custom_target_role',
                'Workflow Transition-custom_responsibility_routing',
                'Workflow Transition-custom_workflow_prompt',
                'Employee-custom_welcome_email_sent_by',
                'Employee-custom_column_break_pihk4',
                'Employee-custom_welcome_email_sent_on',
                'Employee-custom_column_break_eqtxt',
                'Employee-custom_welcome_email_sent_for_joining_date',
                'Employee-custom_welcome_email_information',
                'Company-custom_print_identity_and_colors',
                'Company-custom_print_document_header_color',
                'Company-custom_print_primary_color',
                'Company-custom_column_break_cdpt1',
                'Company-custom_print_accent_color',
                'Company-custom_print_light_color',
                'Company-custom_column_break_twxkf',
                'Company-custom_print_border_color']]]}]

# ==============================================================================
# SHARED COST ALLOCATION
# ==============================================================================
_shared_cost_provisioner = "qorg.qorg.shared_cost_allocation.provisioning.provision_shared_cost_allocation"
if _shared_cost_provisioner not in after_install:
    after_install.append(_shared_cost_provisioner)
if _shared_cost_provisioner not in after_migrate:
    after_migrate.append(_shared_cost_provisioner)
permission_query_conditions["Shared Cost Allocation Run"] = "qorg.qorg.shared_cost_allocation.permissions.allocation_query"

permission_query_conditions["Shared Cost Allocation Rule"] = "qorg.qorg.shared_cost_allocation.permissions.rule_query"

def _qorg_shared_cost_add_event(doctype, event, handler):
    current = doc_events.setdefault(doctype, {}).get(event)
    if not current: doc_events[doctype][event] = handler
    elif isinstance(current, list):
        if handler not in current: current.append(handler)
    elif current != handler: doc_events[doctype][event] = [current, handler]

_qorg_shared_cost_add_event("Project Closure", "before_validate", "qorg.qorg.shared_cost_allocation.closeout.refresh_allocation_closeout")
_qorg_shared_cost_add_event("Project Closure", "validate", "qorg.qorg.shared_cost_allocation.closeout.validate_allocation_closeout")
_qorg_shared_cost_add_event("Project Closure", "on_update", "qorg.qorg.shared_cost_allocation.closeout.lock_rules_after_closure")
permission_query_conditions["Budget Line"] = "qorg.qorg.finance_budget_grants.permissions.budget_line_query"
permission_query_conditions["Commitment Ledger"] = "qorg.qorg.finance_budget_grants.permissions.commitment_ledger_query"
permission_query_conditions["Commitment Entry"] = "qorg.qorg.finance_budget_grants.permissions.commitment_entry_query"
permission_query_conditions["Project Closure"] = "qorg.qorg.finance_budget_grants.permissions.project_closure_query"
has_permission["Budget Line"] = "qorg.qorg.finance_budget_grants.permissions.finance_document_permission"
has_permission["Commitment Ledger"] = "qorg.qorg.finance_budget_grants.permissions.finance_document_permission"
has_permission["Commitment Entry"] = "qorg.qorg.finance_budget_grants.permissions.finance_document_permission"


# Service and allowance accrual foundation
_service_allowance_provisioner = "qorg.qorg.service_allowance.provisioning.provision_service_allowance"
_service_allowance_workflows = "qorg.qorg.service_allowance.workflows.provision_cost_workflows"
if _service_allowance_provisioner not in after_install:
    after_install.append(_service_allowance_provisioner)
if _service_allowance_workflows not in after_install:
    after_install.append(_service_allowance_workflows)
if _service_allowance_provisioner not in after_migrate:
    after_migrate.append(_service_allowance_provisioner)
if _service_allowance_workflows not in after_migrate:
    after_migrate.append(_service_allowance_workflows)

# Generated accounting document integrity
for _event, _handler in {
    "validate": "qorg.qorg.service_allowance.events.validate_generated_journal",
    "on_submit": "qorg.qorg.service_allowance.events.on_submit_generated_journal",
    "on_cancel": "qorg.qorg.service_allowance.events.on_cancel_generated_journal",
}.items():
    _existing = doc_events.setdefault("Journal Entry", {}).get(_event)
    if not _existing:
        doc_events["Journal Entry"][_event] = _handler
    elif isinstance(_existing, list):
        if _handler not in _existing: _existing.append(_handler)
    elif _existing != _handler:
        doc_events["Journal Entry"][_event] = [_existing, _handler]


# Cost Distribution Integration
extend_doctype_class = globals().get("extend_doctype_class", {})
extend_doctype_class.setdefault("Purchase Invoice", []).append("qorg.qorg.cost_distribution.adapters.purchase_invoice.PurchaseInvoiceCostDistributionMixin")
extend_doctype_class.setdefault("Expense Claim", []).append("qorg.qorg.cost_distribution.adapters.expense_claim.ExpenseClaimCostDistributionMixin")
for _dt in ("Material Request","Supplier Quotation","Purchase Order","Purchase Invoice","Expense Claim","Stock Entry","Service Allowance Accrual"):
    _events=doc_events.setdefault(_dt,{})
    for _event,_handler in {"before_validate":"qorg.qorg.cost_distribution.adapters.common.before_validate","before_submit":"qorg.qorg.cost_distribution.adapters.common.before_submit","on_submit":"qorg.qorg.cost_distribution.adapters.common.on_submit","on_cancel":"qorg.qorg.cost_distribution.adapters.common.on_cancel"}.items():
        _current=_events.get(_event)
        if not _current:_events[_event]=_handler
        elif isinstance(_current,list):
            if _handler not in _current:_current.append(_handler)
        elif _current!=_handler:_events[_event]=[_current,_handler]
_hook="qorg.qorg.cost_distribution.provisioning.provision_cost_distribution"
if _hook not in after_install:after_install.append(_hook)
if _hook not in after_migrate:after_migrate.append(_hook)

_cost_distribution_js={"Material Request":"public/js/material_request_cost_distribution.js","Supplier Quotation":"public/js/supplier_quotation_cost_distribution.js","Purchase Order":"public/js/purchase_order_cost_distribution.js","Purchase Invoice":"public/js/purchase_invoice_cost_distribution.js","Expense Claim":"public/js/expense_claim_cost_distribution.js","Stock Entry":"public/js/stock_entry_cost_distribution.js"}
for _dt,_asset in _cost_distribution_js.items():
    _current=doctype_js.get(_dt)
    if not _current:doctype_js[_dt]=_asset
    elif isinstance(_current,list):
        if _asset not in _current:_current.append(_asset)
    elif _current!=_asset:doctype_js[_dt]=[_current,_asset]

for _hook in ("qorg.qorg.cost_distribution.migration.migrate_nested_accrual_distributions",):
    if _hook not in after_migrate:after_migrate.append(_hook)


# Safe post-schema copy migration for shortened Service Allowance names.
_service_allowance_copy_hook = "qorg.qorg.cost_distribution.service_allowance_migration.migrate_service_allowance_names"
if _service_allowance_copy_hook not in after_migrate:
    after_migrate.append(_service_allowance_copy_hook)

_profile_permission_hook = (
    "qorg.qorg.cost_distribution.profile_permissions."
    "repair_profile_submit_permissions"
)

if _profile_permission_hook not in after_migrate:
    after_migrate.append(_profile_permission_hook)

_material_issue_field_hook = "qorg.qorg.inventory_asset_custody.material_request_field_repair.repair_material_request_issue_fields"
if _material_issue_field_hook not in after_migrate:
    after_migrate.append(_material_issue_field_hook)
# Payroll and workforce allocation integration
_payroll_allocation_migrate = "qorg.qorg.payroll_workforce_allocation.migration.migrate"
if _payroll_allocation_migrate not in after_install:
    after_install.append(_payroll_allocation_migrate)
if _payroll_allocation_migrate not in after_migrate:
    after_migrate.append(_payroll_allocation_migrate)

for _doctype, _events in {
    "Payroll Entry": {"validate": "qorg.qorg.payroll_workforce_allocation.events.validate_payroll_entry"},
    "Salary Slip": {
        "on_submit": "qorg.qorg.payroll_workforce_allocation.events.salary_slip_on_submit",
        "on_cancel": "qorg.qorg.payroll_workforce_allocation.events.salary_slip_on_cancel",
    },
}.items():
    doc_events.setdefault(_doctype, {})
    for _event, _handler in _events.items():
        _current = doc_events[_doctype].get(_event)
        if not _current:
            doc_events[_doctype][_event] = _handler
        elif isinstance(_current, list):
            if _handler not in _current: _current.append(_handler)
        elif _current != _handler:
            doc_events[_doctype][_event] = [_current, _handler]

_payroll_salary_slip_js = "public/js/payroll_allocation_salary_slip.js"
_existing_salary_js = doctype_js.get("Salary Slip")
if not _existing_salary_js:
    doctype_js["Salary Slip"] = _payroll_salary_slip_js
elif isinstance(_existing_salary_js, list):
    if _payroll_salary_slip_js not in _existing_salary_js:
        _existing_salary_js.append(_payroll_salary_slip_js)
elif _existing_salary_js != _payroll_salary_slip_js:
    doctype_js["Salary Slip"] = [_existing_salary_js, _payroll_salary_slip_js]

_payroll_daily_job = "qorg.qorg.payroll_workforce_allocation.scheduled_tasks.daily"
scheduler_events.setdefault("daily", [])
if _payroll_daily_job not in scheduler_events["daily"]:
    scheduler_events["daily"].append(_payroll_daily_job)

permission_query_conditions = globals().get("permission_query_conditions", {})
permission_query_conditions.update({
    "Payroll Allocation Run": "qorg.qorg.payroll_workforce_allocation.permissions.payroll_run_query",
    "Workforce Funding Plan": "qorg.qorg.payroll_workforce_allocation.permissions.plan_query",
})
has_permission = globals().get("has_permission", {})
has_permission.update({
    "Payroll Allocation Run": "qorg.qorg.payroll_workforce_allocation.permissions.has_payroll_run_permission",
    "Workforce Funding Plan": "qorg.qorg.payroll_workforce_allocation.permissions.has_plan_permission",
})
for _allocation_doctype in ("Shared Cost Allocation", "Shared Cost Allocation Run", "Cost Distribution", "Cost Distribution Run"):
    doc_events.setdefault(_allocation_doctype, {})
    _guard = "qorg.qorg.payroll_workforce_allocation.guards.validate_other_allocation_document"
    _existing = doc_events[_allocation_doctype].get("validate")
    if not _existing:
        doc_events[_allocation_doctype]["validate"] = _guard
    elif isinstance(_existing, list):
        if _guard not in _existing:
            _existing.append(_guard)
    elif _existing != _guard:
        doc_events[_allocation_doctype]["validate"] = [_existing, _guard]

# Payroll liability payment integration (additive)
for _event,_handler in {
    "validate":"qorg.qorg.payroll_workforce_allocation.payment.validate_payment_entry",
    "on_submit":"qorg.qorg.payroll_workforce_allocation.payment.payment_entry_on_submit",
    "on_cancel":"qorg.qorg.payroll_workforce_allocation.payment.payment_entry_on_cancel",
}.items():
    doc_events.setdefault("Payment Entry",{})
    _current=doc_events["Payment Entry"].get(_event)
    if not _current:doc_events["Payment Entry"][_event]=_handler
    elif isinstance(_current,list):
        if _handler not in _current:_current.append(_handler)
    elif _current!=_handler:doc_events["Payment Entry"][_event]=[_current,_handler]

permission_query_conditions.update({
 "Payroll Cost Policy":"qorg.qorg.payroll_workforce_allocation.permissions.policy_query",
 "Monthly Effort Certification":"qorg.qorg.payroll_workforce_allocation.permissions.effort_query",
})
has_permission.update({
 "Payroll Cost Policy":"qorg.qorg.payroll_workforce_allocation.permissions.has_policy_permission",
 "Monthly Effort Certification":"qorg.qorg.payroll_workforce_allocation.permissions.has_effort_permission",
})

# Payroll allocation standard-form scripts
for _dt,_asset in {
 "Company":"public/js/payroll_company.js",
 "Payroll Entry":"public/js/payroll_entry_allocation.js",
 "Salary Slip":"public/js/payroll_allocation_salary_slip.js",
}.items():
    _current=doctype_js.get(_dt)
    if not _current:doctype_js[_dt]=_asset
    elif isinstance(_current,list):
        if _asset not in _current:_current.append(_asset)
    elif _current!=_asset:doctype_js[_dt]=[_current,_asset]

# QORG EMPLOYEE LIFECYCLE PHASES 7.0-7.5 (additive, idempotent hook registration)
def _qorg_add_doc_event(doctype, event, method):
    current = doc_events.setdefault(doctype, {}).get(event)
    if not current:
        doc_events[doctype][event] = method
    elif isinstance(current, list):
        if method not in current:
            current.append(method)
    elif current != method:
        doc_events[doctype][event] = [current, method]

for _dt, _asset in (
    ("Employee", "public/js/employee_lifecycle.js"),
    ("Employee", "public/js/employee_documents.js"),
    ("Work Commencement Notice", "public/js/work_commencement_lifecycle.js"),
    ("Employee Document Record", "public/js/employee_document_record.js"),
):
    _current = doctype_js.get(_dt)
    if not _current:
        doctype_js[_dt] = _asset
    elif isinstance(_current, list):
        if _asset not in _current:
            _current.append(_asset)
    elif _current != _asset:
        doctype_js[_dt] = [_current, _asset]

# Employee movement script must be added separately because Python dictionaries cannot repeat Employee.
for _asset in ("public/js/employee_movements.js",):
    _current = doctype_js.get("Employee")
    if isinstance(_current, list):
        if _asset not in _current:
            _current.append(_asset)
    elif _current != _asset:
        doctype_js["Employee"] = [_current, _asset] if _current else _asset

for _method in (
    "qorg.qorg.employee_lifecycle.provisioning.provision_employee_lifecycle",
    "qorg.qorg.employee_lifecycle.movement_provisioning.provision_employee_movements",
    "qorg.qorg.employee_lifecycle.document_provisioning.provision_employee_documents",
    "qorg.qorg.employee_lifecycle.separation_clearance.provisioning.provision_employee_separation_clearance",
):
    if _method not in after_migrate:
        after_migrate.append(_method)

_document_daily_job = "qorg.qorg.employee_lifecycle.documents.update_document_statuses"
scheduler_events.setdefault("daily", [])
if _document_daily_job not in scheduler_events["daily"]:
    scheduler_events["daily"].append(_document_daily_job)

permission_query_conditions.update({
    "Employee Document Record": "qorg.qorg.employee_lifecycle.document_permissions.query_condition",
})
has_permission.update({
    "Employee Document Record": "qorg.qorg.employee_lifecycle.document_permissions.has_permission",
})

for _doctype in ("Employee Promotion", "Employee Transfer"):
    _qorg_add_doc_event(_doctype, "validate", "qorg.qorg.employee_lifecycle.movements.validate_employee_movement")
    _qorg_add_doc_event(_doctype, "on_submit", "qorg.qorg.employee_lifecycle.movements.movement_submitted")
    _qorg_add_doc_event(_doctype, "before_cancel", "qorg.qorg.employee_lifecycle.movements.before_cancel_employee_movement")
    _qorg_add_doc_event(_doctype, "on_cancel", "qorg.qorg.employee_lifecycle.movements.movement_cancelled")
_qorg_add_doc_event("Salary Structure Assignment", "validate", "qorg.qorg.employee_lifecycle.movements.validate_salary_assignment")
_qorg_add_doc_event("Workforce Funding Plan", "validate", "qorg.qorg.employee_lifecycle.movements.validate_funding_plan_movement")
_qorg_add_doc_event("Contract Amendment", "validate", "qorg.qorg.employee_lifecycle.movements.validate_contract_amendment_movement")

# EMPLOYEE LIFECYCLE PHASE 7.6B - LEARNING NEEDS AND DEVELOPMENT PLANNING
def _learning_add_js(doctype, asset):
    current = doctype_js.get(doctype)
    if not current:
        doctype_js[doctype] = asset
    elif isinstance(current, list):
        if asset not in current:
            current.append(asset)
    elif current != asset:
        doctype_js[doctype] = [current, asset]

_learning_add_js("Training Need Request", "public/js/training_need_request.js")
_learning_add_js("Development Action", "public/js/development_action.js")

_learning_provisioner = "qorg.qorg.employee_lifecycle.learning_provisioning.provision_learning_planning"
if _learning_provisioner not in after_migrate:
    after_migrate.append(_learning_provisioner)

permission_query_conditions.update({
    "Training Need Request": "qorg.qorg.employee_lifecycle.learning_permissions.training_need_query",
    "Development Action": "qorg.qorg.employee_lifecycle.learning_permissions.development_action_query",
})
has_permission.update({
    "Training Need Request": "qorg.qorg.employee_lifecycle.learning_permissions.training_need_has_permission",
    "Development Action": "qorg.qorg.employee_lifecycle.learning_permissions.development_action_has_permission",
})

# EMPLOYEE LIFECYCLE PHASE 7.6C - TRAINING EXECUTION AND EFFECTIVENESS
_learning_add_js("Training Assessment", "public/js/training_assessment.js")
_learning_add_js("Training Follow-up", "public/js/training_follow_up.js")
_learning_add_js("Training Event", "public/js/training_event_ext.js")
_training_setup = "qorg.qorg.employee_lifecycle.training_setup.setup_training_execution"
if _training_setup not in after_migrate:
    after_migrate.append(_training_setup)
_training_daily = "qorg.qorg.employee_lifecycle.training.update_overdue_follow_ups"
scheduler_events.setdefault("daily", [])
if _training_daily not in scheduler_events["daily"]:
    scheduler_events["daily"].append(_training_daily)
permission_query_conditions.update({
    "Training Assessment": "qorg.qorg.employee_lifecycle.training_perm.assessment_query",
    "Training Follow-up": "qorg.qorg.employee_lifecycle.training_perm.follow_up_query",
})
has_permission.update({
    "Training Assessment": "qorg.qorg.employee_lifecycle.training_perm.assessment_has_permission",
    "Training Follow-up": "qorg.qorg.employee_lifecycle.training_perm.follow_up_has_permission",
})

# EMPLOYEE LIFECYCLE PHASE 7.6D - EVALUATION POLICY AND ASSIGNMENTS
_learning_add_js("Evaluation Type", "public/js/evaluation_type.js")
_learning_add_js("Evaluation Assignment", "public/js/evaluation_assignment.js")
_learning_add_js("Appraisal", "public/js/appraisal_ext.js")
_learning_add_js("Appraisal Cycle", "public/js/appraisal_cycle_ext.js")
_performance_setup = "qorg.qorg.employee_lifecycle.perf_setup.setup_performance_policy"
if _performance_setup not in after_migrate:
    after_migrate.append(_performance_setup)
permission_query_conditions.update({
    "Evaluation Assignment": "qorg.qorg.employee_lifecycle.perf_perm.assignment_query",
})
has_permission.update({
    "Evaluation Assignment": "qorg.qorg.employee_lifecycle.perf_perm.assignment_has_permission",
})
_qorg_add_doc_event("Appraisal Cycle", "validate", "qorg.qorg.employee_lifecycle.performance.validate_appraisal_cycle")
_qorg_add_doc_event("Employee Performance Feedback", "validate", "qorg.qorg.employee_lifecycle.performance.validate_feedback")
_qorg_add_doc_event("Employee Performance Feedback", "on_submit", "qorg.qorg.employee_lifecycle.performance.feedback_submitted")
_qorg_add_doc_event("Employee Performance Feedback", "on_cancel", "qorg.qorg.employee_lifecycle.performance.feedback_cancelled")

# EMPLOYEE LIFECYCLE PHASE 7.6E - APPRAISAL LIFECYCLE AND CALCULATION
_qorg_add_doc_event("Appraisal", "before_submit", "qorg.qorg.employee_lifecycle.performance.before_submit_appraisal")
_qorg_add_doc_event("Appraisal", "on_submit", "qorg.qorg.employee_lifecycle.performance.appraisal_submitted")
_qorg_add_doc_event("Appraisal", "on_cancel", "qorg.qorg.employee_lifecycle.performance.appraisal_cancelled")
_qorg_add_doc_event("Appraisal", "validate", "qorg.qorg.employee_lifecycle.performance.protect_appraisal")

# EMPLOYEE LIFECYCLE PHASE 7.6F - SKILLS, RECOMMENDATIONS AND HISTORY
_learning_add_js("Employee", "public/js/employee_dev.js")
_development_setup = "qorg.qorg.employee_lifecycle.dev_setup.setup_development"
if _development_setup not in after_migrate:
    after_migrate.append(_development_setup)
_qorg_add_doc_event("Training Program", "validate", "qorg.qorg.employee_lifecycle.training.validate_training_policy")
_qorg_add_doc_event("Training Event", "validate", "qorg.qorg.employee_lifecycle.training.validate_training_policy")
_learning_add_js("Employee Performance Feedback", "public/js/performance_feedback_ext.js")
_learning_add_js("Training Follow-up", "public/js/learning_comms.js")
_learning_add_js("Training Result", "public/js/learning_comms.js")
_learning_add_js("Evaluation Assignment", "public/js/learning_comms.js")
_learning_add_js("Appraisal", "public/js/learning_comms.js")
_learning_comms_setup = "qorg.qorg.employee_lifecycle.comms.provision_communications"
if _learning_comms_setup not in after_migrate:
    after_migrate.append(_learning_comms_setup)
# Multi-period budget control
def _qorg_add_doc_event(doctype, event, method):
    current = doc_events.setdefault(doctype, {}).get(event)
    if not current: doc_events[doctype][event] = method
    elif isinstance(current, list):
        if method not in current: current.append(method)
    elif current != method: doc_events[doctype][event] = [current, method]
_qorg_add_doc_event("Budget Line", "validate", "qorg.qorg.finance_period_control.service.validate_budget_line")
_qorg_add_doc_event("Commitment Ledger", "validate", "qorg.qorg.finance_period_control.service.validate_commitment_ledger")
_qorg_add_doc_event("Commitment Ledger", "on_update", "qorg.qorg.finance_period_control.projection.refresh_for_ledger")
_qorg_add_doc_event("Commitment Ledger", "on_cancel", "qorg.qorg.finance_period_control.projection.refresh_for_ledger")
_projection_js = "public/js/budget_line_projection.js"
_current_projection_js = doctype_js.get("Budget Line")
if not _current_projection_js:
    doctype_js["Budget Line"] = _projection_js
elif isinstance(_current_projection_js, list):
    if _projection_js not in _current_projection_js: _current_projection_js.append(_projection_js)
elif _current_projection_js != _projection_js:
    doctype_js["Budget Line"] = [_current_projection_js, _projection_js]
_qorg_add_doc_event("Budget Line", "on_update", "qorg.qorg.finance_period_control.budget_sync.mark_unsynced")
_sync_js = "public/js/budget_line_sync.js"
_current_sync_js = doctype_js.get("Budget Line")
if not _current_sync_js:
    doctype_js["Budget Line"] = _sync_js
elif isinstance(_current_sync_js, list):
    if _sync_js not in _current_sync_js: _current_sync_js.append(_sync_js)
elif _current_sync_js != _sync_js:
    doctype_js["Budget Line"] = [_current_sync_js, _sync_js]
for _dt in ("Budget Period", "Budget Period Resolution Rule", "Commitment Ledger"):
    _asset = "public/js/finance_period_control.js"
    _current = doctype_js.get(_dt)
    if not _current: doctype_js[_dt] = _asset
    elif isinstance(_current, list):
        if _asset not in _current: _current.append(_asset)
    elif _current != _asset: doctype_js[_dt] = [_current, _asset]
_finance_control_asset = "public/js/finance_period_control.js"
_current_bl_assets = doctype_js.get("Budget Line")
if isinstance(_current_bl_assets, list):
    if _finance_control_asset not in _current_bl_assets: _current_bl_assets.append(_finance_control_asset)
elif _current_bl_assets and _current_bl_assets != _finance_control_asset:
    doctype_js["Budget Line"] = [_current_bl_assets, _finance_control_asset]
elif not _current_bl_assets: doctype_js["Budget Line"] = _finance_control_asset
_qorg_add_doc_event("Purchase Receipt", "on_submit", "qorg.qorg.finance_period_control.routing_v2.purchase_receipt_submit")
_qorg_add_doc_event("Purchase Receipt", "on_cancel", "qorg.qorg.finance_period_control.settlement_v2.cancel_source")
_qorg_add_doc_event("Purchase Invoice", "on_update_after_submit", "qorg.qorg.finance_period_control.gl_matching_v2.reconcile_on_update_after_submit")
_qorg_add_doc_event("Purchase Order", "on_update_after_submit", "qorg.qorg.finance_period_control.returns_v2.close_purchase_order")
_qorg_add_doc_event("Purchase Order", "validate", "qorg.qorg.finance_period_control.procurement_route.validate")
_qorg_add_doc_event("Purchase Invoice", "validate", "qorg.qorg.finance_period_control.procurement_route.validate")
for _dt in ("Material Request", "Purchase Order", "Purchase Invoice"):
    _asset = "public/js/direct_procurement.js"
    _current = doctype_js.get(_dt)
    if not _current: doctype_js[_dt] = _asset
    elif isinstance(_current, list):
        if _asset not in _current: _current.append(_asset)
    elif _current != _asset: doctype_js[_dt] = [_current, _asset]
for _dt in ("Purchase Order", "Purchase Invoice", "Purchase Receipt"):
    _qorg_add_doc_event(_dt, "validate", "qorg.qorg.finance_period_control.distribution_bridge.validate_distribution")
_period_close_js = "public/js/budget_period_closure.js"
_current_period_js = doctype_js.get("Budget Period")
if isinstance(_current_period_js, list):
    if _period_close_js not in _current_period_js: _current_period_js.append(_period_close_js)
elif _current_period_js and _current_period_js != _period_close_js: doctype_js["Budget Period"] = [_current_period_js, _period_close_js]
elif not _current_period_js: doctype_js["Budget Period"] = _period_close_js
for _dt in ("Material Request", "Purchase Order", "Purchase Invoice"):
    _qorg_add_doc_event(_dt, "validate", "qorg.qorg.finance_period_control.policy_v2.validate_document")
_qorg_add_doc_event("Material Request", "validate", "qorg.qorg.finance_period_control.procurement_route.validate")
