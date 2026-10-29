app_name = "qorg"
app_title = "Q Org"
app_publisher = "Q Org"
app_description = "Audit-focused extensions for ERPNext"
app_email = ""
app_license = "GPL-3.0"

app_logo_url = "/assets/qorg/images/qorg_project_cycle.png"
app_home = "/desk/q-management-hub"

add_to_apps_screen = [{
    "name": app_name,
    "logo": app_logo_url,
    "title": "Q Org",
    "route": app_home,
    "sequence_id": 5,
}]

required_apps = ["erpnext", "hrms"]

extend_bootinfo = "qorg.qorg.enterprise_foundation.boot.extend_bootinfo"

app_include_js = [
    "/assets/qorg/js/qorg_form_bootstrap.js",
    "/assets/qorg/js/model_policy.js",
]

app_include_css = [
    "/assets/qorg/css/model_policy.css",
]

web_include_css = [
    "/assets/qorg/css/web_form_design_system.css",
]

web_include_js = [
    "/assets/qorg/js/web_form_design_system.js",
]

website_route_rules = [
    {"from_route": "/opportunities/<route>", "to_route": "opportunities/detail"},
]

override_whitelisted_methods = {
    "frappe.model.rename_doc.update_document_title": (
        "qorg.qorg.enterprise_foundation.overrides.update_document_title"
    ),
}

extend_doctype_class = {
    "Task": [
        "qorg.qorg.task_management.task_controller.TaskProjectPeriodPolicyMixin"
    ],
}

doctype_js = {
    "Website Settings": "public/js/website_settings_opportunity_portal.js",
    "Web Form": "public/js/web_form_design_settings.js",
    "HR Settings": "public/js/hr_settings_recruitment.js",
    "Designation": "public/js/designation_recruitment.js",
    "Interview Type": "public/js/interview_type.js",
    "Interview Feedback": "public/js/interview_feedback.js",
    "Job Applicant": "public/js/job_applicant_recruitment.js",
    "Task Assignment Request": "public/js/task_assignment_request.js",
    "Task": "public/js/task.js",
    "Employee": "public/js/employee_announcement.js",
    "Notification": "public/js/notification_configuration.js",
    "Workflow": "public/js/workflow_engine.js",
    "Projects Settings": "public/js/projects_settings.js",
    "Print Settings": "public/js/print_settings.js",
}

doc_events = {
    "Designation": {"validate": [
        "qorg.qorg.recruitment_extensions.events.designation_validate",
        "qorg.qorg.recruitment_extensions.validation.validate_designation",
    ]},
    "External Person": {
        "on_update": (
            "qorg.qorg.people_and_opportunities.portal_settings."
            "sync_external_person_portal_access"
        ),
        "on_trash": (
            "qorg.qorg.people_and_opportunities.integrity."
            "prevent_operational_delete"
        ),
    },
    "External Opportunity": {
        "validate": [
            "qorg.qorg.volunteer_management.events.validate_external_opportunity",
            (
                "qorg.qorg.people_and_opportunities.portal."
                "validate_external_opportunity_publication"
            ),
        ],
        "on_update": (
            "qorg.qorg.people_and_opportunities.portal."
            "handle_external_opportunity_publication"
        ),
        "on_trash": (
            "qorg.qorg.people_and_opportunities.integrity."
            "prevent_operational_delete"
        ),
    },
    "Participation Application": {
        "on_trash": "qorg.qorg.volunteer_management.integrity.prevent_operational_delete",
    },
    "Participation Assessment": {
        "on_trash": "qorg.qorg.volunteer_management.integrity.prevent_operational_delete",
    },
    "Participation Engagement": {
        "on_trash": "qorg.qorg.volunteer_management.integrity.prevent_operational_delete",
    },
    "Participation Service Log": {
        "on_trash": "qorg.qorg.volunteer_management.integrity.prevent_operational_delete",
    },
    "Participation Evaluation": {
        "on_trash": "qorg.qorg.volunteer_management.integrity.prevent_operational_delete",
    },
    "Participation Certificate": {
        "on_trash": "qorg.qorg.volunteer_management.integrity.prevent_operational_delete",
    },
    "Volunteer Profile": {"on_trash": "qorg.qorg.people_and_opportunities.integrity.prevent_operational_delete"},
    "External Opportunity Type": {"on_trash": "qorg.qorg.people_and_opportunities.integrity.prevent_master_delete"},
    "Person Qualification": {"on_trash": "qorg.qorg.people_and_opportunities.integrity.prevent_master_delete"},
    "Volunteer Category": {"on_trash": "qorg.qorg.people_and_opportunities.integrity.prevent_master_delete"},
    "Job Opening": {
        "validate": [
            "qorg.qorg.people_and_opportunities.integrations.validate_job_opening",
            "qorg.qorg.recruitment_extensions.events.opening_validate",
            "qorg.qorg.recruitment_extensions.defaults.apply_job_opening_defaults",
            "qorg.qorg.recruitment_extensions.validation.validate_job_opening",
        ],
    },
    "Job Applicant": {
        "before_validate": [
            "qorg.qorg.people_and_opportunities.integrations.sync_job_applicant_person",
            "qorg.qorg.recruitment_extensions.defaults.validate_job_applicant_policy",
            "qorg.qorg.recruitment_extensions.events.applicant_validate",
        ],
        "on_update": "qorg.qorg.people_and_opportunities.integrations.sync_job_applicant_person",
    },
    "Interview Type": {"validate": [
        "qorg.qorg.recruitment_extensions.defaults.apply_interview_type_defaults",
        "qorg.qorg.recruitment_extensions.events.interview_type_validate",
        "qorg.qorg.recruitment_extensions.validation.validate_interview_type",
    ]},
    "Interview Feedback": {
        "before_validate": [
            "qorg.qorg.recruitment_extensions.events.feedback_validate",
            "qorg.qorg.recruitment_extensions.defaults.validate_feedback_policy",
            "qorg.qorg.recruitment_extensions.validation.validate_feedback",
        ],
        "on_submit": "qorg.qorg.recruitment_extensions.events.feedback_submit",
        "on_cancel": "qorg.qorg.recruitment_extensions.events.feedback_cancel",
        "after_delete": "qorg.qorg.recruitment_extensions.events.feedback_delete",
    },
    "Interview": {
        "validate": [
            "qorg.qorg.recruitment_extensions.defaults.apply_interview_defaults",
            "qorg.qorg.recruitment_extensions.events.interview_validate",
        ],
        "on_cancel": "qorg.qorg.recruitment_extensions.events.interview_cancel",
        "on_trash": "qorg.qorg.recruitment_extensions.events.interview_trash",
    },
    "Job Offer": {
        "before_validate": [
            "qorg.qorg.recruitment_extensions.defaults.apply_job_offer_defaults",
            "qorg.qorg.recruitment_extensions.events.offer_before_validate",
        ],
        "on_update": "qorg.qorg.recruitment_extensions.events.offer_on_update",
    },
    "Appointment Letter": {
        "validate": "qorg.qorg.recruitment_extensions.events.appointment_validate",
        "on_update": "qorg.qorg.recruitment_extensions.events.appointment_on_update",
    },
    "Employee": {
        "validate": "qorg.qorg.recruitment_extensions.events.employee_validate",
        "after_insert": "qorg.qorg.recruitment_extensions.events.employee_after_insert",
    },
    "Employee Onboarding": {
        "before_validate": "qorg.qorg.recruitment_extensions.defaults.apply_onboarding_defaults",
        "validate": [
            "qorg.qorg.recruitment_extensions.events.onboarding_validate",
            "qorg.qorg.recruitment_extensions.onboarding.validate_onboarding",
        ],
    },
    "Website Settings": {
        "validate": (
            "qorg.qorg.people_and_opportunities.portal_settings."
            "validate_website_settings"
        ),
    },
    "HR Settings": {
        "validate": "qorg.qorg.recruitment_extensions.settings.validate_hr_settings"
    },
    "Print Settings": {
        "validate": "qorg.qorg.project_management.print_settings_integration.validate_print_settings",

    },
    "Project Risk": {
        "on_update": (
            "qorg.qorg.project_management.notification_engine."
            "process_project_notification_on_update"
        )
    },
    "Task": {
        "before_validate": "qorg.qorg.task_management.events.before_validate",
        "on_update": "qorg.qorg.task_management.events.on_update",
        "after_delete": "qorg.qorg.task_management.events.after_delete",
    },
    "Workflow": {
        "validate": (
            "qorg.qorg.workflow.provisioning."
            "validate_workflow_configuration"
        ),
        "on_update": (
            "qorg.qorg.workflow.provisioning."
            "ensure_current_responsible_user"
        ),
    },
    "*": {
        "before_insert": "qorg.qorg.enterprise_foundation.policy_enforcement.enforce_model_policy",
        "before_save": "qorg.qorg.enterprise_foundation.policy_enforcement.enforce_model_policy",
        "before_submit": "qorg.qorg.enterprise_foundation.policy_enforcement.enforce_model_policy",
        "before_cancel": "qorg.qorg.enterprise_foundation.policy_enforcement.enforce_model_policy",
        "before_update_after_submit": "qorg.qorg.enterprise_foundation.policy_enforcement.enforce_model_policy",
        "on_trash": "qorg.qorg.enterprise_foundation.policy_enforcement.enforce_model_policy",
        "validate": (
            "qorg.qorg.workflow.permissions."
            "validate_responsible_user"
        ),
    },
}

fixtures = [
    {"dt": "Custom Field", "filters": [["name", "in", [
        "Workflow Transition-custom_employee_signature_mapping_key",
        "Workflow Transition-custom_apply_employee_signature",
        "Workflow Transition-custom_notify_document_creator",
        "Workflow Transition-custom_column_break_6mqhf",
        "Workflow Transition-custom_section_break_h8b1r",
        "Workflow Transition-custom_target_role",
        "Workflow Transition-custom_target_user_field",
        "Workflow Transition-custom_workflow_prompt",
        "Workflow Transition-custom_assignment_required",
        "Employee-custom_welcome_email_sent_by",
        "Employee-custom_column_break_pihk4",
        "Employee-custom_welcome_email_sent_on",
        "Employee-custom_column_break_eqtxt",
        "Employee-custom_welcome_email_sent_for_joining_date",
        "Employee-custom_welcome_email_information",
        "Workflow-custom_current_responsible_user_field",
        "Company-custom_print_identity_and_colors",
        "Company-custom_print_document_header_color",
        "Company-custom_print_primary_color",
        "Company-custom_column_break_cdpt1",
        "Company-custom_print_accent_color",
        "Company-custom_print_light_color",
        "Company-custom_column_break_twxkf",
        "Company-custom_print_border_color",
    ]]]},
]

before_migrate = [
    "qorg.qorg.project_management.identity_migration.prepare_q_org_identity",
    "qorg.qorg.project_management.workspace_migration.prepare_q_management_hub",
]

after_install = [
    "qorg.qorg.recruitment_extensions.settings_provisioning.provision_recruitment_settings",

    "qorg.qorg.recruitment_extensions.provisioning.provision_recruitment_extensions",
    "qorg.qorg.people_and_opportunities.provisioning.provision_people_opportunities_core",
    "qorg.qorg.people_and_opportunities.portal_provisioning.provision_opportunity_portal",
    "qorg.qorg.volunteer_management.provisioning.provision_volunteer_management",
    "qorg.qorg.project_management.print_settings_integration.provision_print_settings",
    "qorg.qorg.install.after_install",
    "qorg.qorg.task_management.provisioning.provision_task_integration",
    "qorg.qorg.project_management.provisioning.provision_project_management",
    "qorg.qorg.project_management.workflow_provisioning.provision_project_workflows",
    "qorg.qorg.project_management.notification_provisioning.provision_project_notifications",
    "qorg.qorg.enterprise_foundation.provisioning.provision_enterprise_foundation",
    "qorg.qorg.project_management.navigation_provisioning.provision_q_org_navigation",
]

after_migrate = [
    "qorg.qorg.recruitment_extensions.settings_provisioning.provision_recruitment_settings",

    "qorg.qorg.recruitment_extensions.provisioning.provision_recruitment_extensions",
    "qorg.qorg.people_and_opportunities.provisioning.provision_people_opportunities_core",
    "qorg.qorg.people_and_opportunities.portal_provisioning.provision_opportunity_portal",
    "qorg.qorg.volunteer_management.provisioning.provision_volunteer_management",
    "qorg.qorg.project_management.print_settings_integration.provision_print_settings",
    "qorg.qorg.install.after_migrate",
    "qorg.printing.provisioning.provision_universal_print_formats",
    "qorg.qorg.project_management.print_settings_cleanup.remove_legacy_print_settings",
    "qorg.qorg.task_management.provisioning.provision_task_integration",
    "qorg.qorg.project_management.provisioning.provision_project_management",
    "qorg.qorg.project_management.workflow_provisioning.provision_project_workflows",
    "qorg.qorg.project_management.notification_provisioning.provision_project_notifications",
    "qorg.qorg.enterprise_foundation.provisioning.provision_enterprise_foundation",
    "qorg.qorg.project_management.navigation_provisioning.provision_q_org_navigation",
]

scheduler_events = {
    "daily": [
        "qorg.qorg.recruitment_extensions.settings_jobs.run_daily_recruitment_settings_jobs",
        "qorg.qorg.people_and_opportunities.portal_scheduler.close_expired_public_opportunities",
        "qorg.qorg.project_management.notification_engine.run_daily_project_notifications",
        "qorg.qorg.project_management.integrity_jobs.run_daily_project_reconciliation",
    ],
    "cron": {
        "*/15 * * * *": [
            "qorg.qorg.task_management.scheduler.run_scheduled_task_summary"
        ]
    },
}

standard_portal_menu_items = [
    {
        "title": "Opportunities",
        "route": "/opportunities",
        "reference_doctype": "External Opportunity",
    },
    {
        "title": "My Applications",
        "route": "/my-applications",
        "reference_doctype": "Participation Application",
        "role": "External Applicant",
    },
    {
        "title": "My Profile",
        "route": "/external-profile",
        "reference_doctype": "External Person",
        "role": "External Applicant",
    },
]

role_home_page = {
    "External Applicant": "opportunities",
}

permission_query_conditions = {
    "Task": "qorg.qorg.task_management.permissions.task_query_condition",
    "Task Assignment Request": (
        "qorg.qorg.task_management.permissions.request_query_condition"
    ),
}

has_permission = {
    "Feature Control Center": "qorg.qorg.enterprise_foundation.permissions.feature_control_center_has_permission",
    "Managed Configuration State": "qorg.qorg.enterprise_foundation.permissions.managed_state_has_permission",
    "Task": "qorg.qorg.task_management.permissions.has_task_permission",
    "Task Assignment Request": (
        "qorg.qorg.task_management.permissions.has_request_permission"
    ),
}
