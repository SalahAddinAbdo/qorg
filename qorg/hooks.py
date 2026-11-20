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

override_doctype_dashboards = {'Material Request': 'qorg.qorg.dashboards.material_request.get_data'}

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
 'Procurement Complaint': ['public/js/procurement_complaint.js']}

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
 'Volunteer Profile': {'on_trash': 'qorg.qorg.people_and_opportunities.integrity.prevent_operational_delete',
                       'validate': 'qorg.qorg.volunteer_management.cycle_integrity.validate_volunteer_record'},
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
                      'on_submit': ['qorg.qorg.procurement_contracting.commitment_hooks.invoice_submit'],
                      'on_cancel': ['qorg.qorg.procurement_contracting.commitment_hooks.invoice_cancel']},
 'Supplier Registration': {'validate': ['qorg.qorg.procurement_contracting.supplier_profile.validate_supplier_registration']},
 'Material Request': {'on_submit': ['qorg.qorg.procurement_contracting.routing.route_material_request',
                                    'qorg.qorg.procurement_contracting.commitment_hooks.material_request_submit'],
                      'on_cancel': ['qorg.qorg.procurement_contracting.commitment_hooks.material_request_cancel'],
                      'validate': ['qorg.qorg.inventory_asset_custody.issue_control.validate_material_request_activity',
                                   'qorg.qorg.finance_budget_grants.services.validate_accounting_document']},
 'Procurement Contract': {'validate': ['qorg.qorg.procurement_contracting.contract_engine.validate_contract'],
                          'on_submit': ['qorg.qorg.procurement_contracting.commitment_hooks.contract_submit'],
                          'on_cancel': ['qorg.qorg.procurement_contracting.commitment_hooks.contract_cancel']},
 'Framework Call Off': {'validate': ['qorg.qorg.procurement_contracting.contract_engine.validate_framework_call_off']},
 'Procurement Submission': {'validate': ['qorg.qorg.procurement_contracting.submission_service.validate_submission']},
 'Purchase Order': {'on_submit': ['qorg.qorg.procurement_contracting.commitment_hooks.purchase_order_submit'],
                    'on_cancel': ['qorg.qorg.procurement_contracting.commitment_hooks.purchase_order_cancel'],
                    'validate': ['qorg.qorg.procurement_contracting.standard_guards.validate_purchase_order',
                                 'qorg.qorg.procurement_contracting.standard_guards.validate_contract_links',
                                 'qorg.qorg.finance_budget_grants.services.validate_accounting_document']},
 'Procure Acceptance': {'on_submit': ['qorg.qorg.procurement_contracting.commitment_hooks.acceptance_submit'],
                        'on_cancel': ['qorg.qorg.procurement_contracting.commitment_hooks.acceptance_cancel'],
                        'validate': ['qorg.qorg.procurement_contracting.contract_engine.validate_acceptance']},
 'Payment Entry': {'on_submit': ['qorg.qorg.procurement_contracting.commitment_hooks.payment_submit'],
                   'on_cancel': ['qorg.qorg.procurement_contracting.commitment_hooks.payment_cancel'],
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
                                      'qorg.qorg.recruitment_extensions.employee_cycle_integrity.prevent_incomplete_employee_exit']},
 'Employee Offboarding': {'validate': ['qorg.qorg.inventory_asset_custody.asset_control.prevent_separation',
                                       'qorg.qorg.recruitment_extensions.employee_cycle_integrity.prevent_incomplete_employee_exit']},
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
 'Volunteer Application': {'validate': 'qorg.qorg.volunteer_management.cycle_integrity.validate_volunteer_record'},
 'Volunteer Engagement': {'validate': 'qorg.qorg.volunteer_management.cycle_integrity.validate_volunteer_record'},
 'Work Commencement Notice': {'validate': 'qorg.qorg.recruitment_extensions.employee_cycle_integrity.validate_work_commencement'},
 'Journal Entry': {'validate': 'qorg.qorg.finance_budget_grants.services.validate_accounting_document'},
 'Expense Claim': {'validate': 'qorg.qorg.finance_budget_grants.services.validate_accounting_document'},
 'Payroll Entry': {'validate': 'qorg.qorg.finance_budget_grants.services.validate_accounting_document'},
 'Salary Slip': {'validate': 'qorg.qorg.finance_budget_grants.services.validate_accounting_document'},
 'Budget Line': {'before_validate': 'qorg.qorg.finance_budget_grants.services.apply_budget_line_defaults',
                 'validate': 'qorg.qorg.finance_budget_grants.services.validate_budget_line'},
 'Project': {'validate': 'qorg.qorg.finance_budget_grants.services.validate_project_funding_source'},
 'Funding Agreement': {'on_update': 'qorg.qorg.finance_budget_grants.budget_transfers.sync_funding_agreement_to_project'}}

# ==============================================================================
# PERMISSIONS
# ==============================================================================

permission_query_conditions = {'Task': 'qorg.qorg.task_management.permissions.task_query_condition',
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

has_permission = {'Feature Control Center': 'qorg.qorg.enterprise_foundation.permissions.feature_control_center_has_permission',
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

scheduler_events = {'daily': ['qorg.qorg.recruitment_extensions.settings_jobs.run_daily_recruitment_settings_jobs',
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

after_migrate = ['qorg.qorg.finance_budget_grants.provisioning.provision_finance_budget_grants',
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
