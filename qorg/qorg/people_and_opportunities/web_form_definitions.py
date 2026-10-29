from __future__ import annotations

MANAGED_VERSION = "1.0.0"

PROFILE_FIELDS = [
    "first_name", "middle_name", "last_name", "full_name", "primary_email",
    "alternate_email", "mobile_no", "phone", "date_of_birth", "nationality",
    "country", "governorate", "city", "address", "profile_summary", "resume",
    "professional_summary", "education", "work_experience", "experience",
    "skills", "languages", "training", "certifications", "volunteer_experience",
    "references", "documents",
]

PARTICIPATION_FIELDS = [
    "opportunity", "external_person", "participation_type", "application_date",
    "motivation", "relevant_experience", "available_from", "available_to",
    "hours_per_week", "accommodation_needs",
    "application_source", "status",
]

EMPLOYMENT_FIELDS = [
    "qorg_external_opportunity", "qorg_external_person", "job_title", "applicant_name",
    "email_id", "phone_number", "cover_letter", "resume_attachment", "resume",
    "status", "source",
]

PROFILE_SCRIPT = r'''
frappe.web_form.after_load = async () => {
  try {
    const result = await frappe.call({
      method: "qorg.qorg.people_and_opportunities.web_form_services.get_profile_web_form_state"
    });
    const state = result.message || {};
    if (state.name && window.location.pathname.endsWith("/new")) {
      window.location.replace(`/external-profile-form/${encodeURIComponent(state.name)}/edit`);
      return;
    }
    if (state.locked) {
      frappe.msgprint({
        title: __("Profile editing is locked"),
        message: state.lock_reason || __("Contact the organization if a profile update is required."),
        indicator: "orange"
      });
    }
  } catch (error) {
    console.error(error);
  }
};
'''

APPLICATION_SCRIPT = r'''
frappe.web_form.after_load = async () => {
  const params = new URLSearchParams(window.location.search);
  const route = params.get("opportunity_route");
  if (!route) {
    frappe.msgprint(__("Open the application form from a published opportunity."));
    return;
  }
  try {
    const result = await frappe.call({
      method: "qorg.qorg.people_and_opportunities.web_form_services.get_application_web_form_context",
      args: { opportunity_route: route, target_doctype: frappe.web_form.doc_type }
    });
    const context = result.message || {};
    if (!context.open) {
      frappe.msgprint(context.message || __("Applications are closed for this opportunity."));
      return;
    }
    Object.entries(context.values || {}).forEach(([fieldname, value]) => {
      if (value !== undefined && value !== null) {
        frappe.web_form.set_value(fieldname, value);
      }
    });
  } catch (error) {
    console.error(error);
  }
};

frappe.web_form.validate = () => {
  const params = new URLSearchParams(window.location.search);
  if (!params.get("opportunity_route")) {
    frappe.msgprint(__("The opportunity reference is missing."));
    return false;
  }
  return true;
};
'''

WEB_FORMS = [
    {
        "key": "external_profile",
        "title": "External Profile",
        "route": "external-profile-form",
        "doc_type": "External Person",
        "login_required": 1,
        "allow_multiple": 0,
        "allow_edit": 1,
        "allow_delete": 0,
        "show_list": 0,
        "allow_print": 1,
        "introduction_text": "Create and maintain one professional profile for employment, volunteering, and internship applications.",
        "success_message": "Your professional profile has been saved successfully.",
        "client_script": PROFILE_SCRIPT,
        "candidate_fields": PROFILE_FIELDS,
        "required_fields": ["first_name", "full_name", "primary_email"],
        "read_only_fields": ["full_name"],
        "remove_fields": [],
    },
    {
        "key": "participation_application",
        "title": "Participation Application",
        "route": "participation-application",
        "doc_type": "Participation Application",
        "login_required": 1,
        "allow_multiple": 1,
        "allow_edit": 1,
        "allow_delete": 0,
        "show_list": 1,
        "allow_print": 1,
        "introduction_text": "Apply for a volunteering or internship opportunity using your saved external profile.",
        "success_message": "Your participation application has been submitted successfully.",
        "client_script": APPLICATION_SCRIPT,
        "candidate_fields": PARTICIPATION_FIELDS,
        "required_fields": ["opportunity", "motivation"],
        "read_only_fields": ["opportunity", "external_person", "participation_type", "application_date", "applicant_name", "email", "mobile_no", "status", "application_source"],
        "remove_fields": [],
    },
    {
        "key": "employment_application",
        "title": "Employment Application",
        "route": "employment-application",
        "doc_type": "Job Applicant",
        "login_required": 1,
        "allow_multiple": 1,
        "allow_edit": 1,
        "allow_delete": 0,
        "show_list": 1,
        "allow_print": 1,
        "introduction_text": "Apply for an employment opportunity using your saved external profile.",
        "success_message": "Your employment application has been submitted successfully.",
        "client_script": APPLICATION_SCRIPT,
        "candidate_fields": EMPLOYMENT_FIELDS,
        "required_fields": ["job_title", "applicant_name", "email_id"],
        "read_only_fields": ["qorg_external_opportunity", "qorg_external_person", "job_title", "applicant_name", "email_id", "phone_number", "status", "source"],
        "remove_fields": [],
    },
]
