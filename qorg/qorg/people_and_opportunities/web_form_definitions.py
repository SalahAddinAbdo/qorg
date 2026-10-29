from __future__ import annotations

MANAGED_VERSION = "2.0.0"

WEB_FORMS = [
    {
        "title": "External Profile",
        "route": "external-profile-form",
        "doc_type": "External Person",
        "allow_multiple": 0,
        "allow_edit": 1,
        "show_list": 0,
        "allow_print": 1,
        "introduction_text": "Create and maintain one professional profile for employment, volunteering, and internship applications.",
        "success_message": "Your professional profile has been saved successfully.",
        "candidate_fields": [
            "first_name", "middle_name", "last_name", "full_name", "name_in_arabic",
            "primary_email", "secondary_email", "mobile_no", "alternative_mobile_no",
            "current_location", "preferred_contact_method", "preferred_language",
            "identification_type", "identification_number", "identification_country",
            "date_of_birth", "nationality", "marital_status", "gender", "image",
            "professional_title", "years_of_experience", "availability_status",
            "professional_summary", "career_objective", "sectors_of_expertise",
            "key_achievements", "education", "experience", "training", "languages",
            "skills", "volunteer_experience", "references", "resume", "portfolio_url",
            "linkedin_url", "privacy_consent",
        ],
        "required_fields": ["first_name", "primary_email", "privacy_consent"],
        "read_only_fields": ["full_name"],
    },
    {
        "title": "Participation Application",
        "route": "participation-application",
        "doc_type": "Participation Application",
        "allow_multiple": 1,
        "allow_edit": 1,
        "show_list": 1,
        "allow_print": 1,
        "introduction_text": "Apply for a volunteering or internship opportunity using your saved external profile.",
        "success_message": "Your participation application has been submitted successfully.",
        "candidate_fields": [
            "opportunity", "external_person", "participation_type", "application_date",
            "status", "available_from", "available_to", "hours_per_week", "motivation",
            "relevant_experience", "accommodation_needs",
        ],
        "required_fields": ["opportunity", "motivation"],
        "read_only_fields": [
            "opportunity", "external_person", "participation_type", "application_date", "status"
        ],
    },
    {
        "title": "Employment Application",
        "route": "employment-application",
        "doc_type": "Job Applicant",
        "allow_multiple": 1,
        "allow_edit": 1,
        "show_list": 1,
        "allow_print": 1,
        "introduction_text": "Apply for an employment opportunity using your saved external profile.",
        "success_message": "Your employment application has been submitted successfully.",
        "candidate_fields": [
            "qorg_external_opportunity", "qorg_external_person", "job_title",
            "applicant_name", "email_id", "phone_number", "cover_letter",
            "resume_attachment", "resume", "status", "source",
        ],
        "required_fields": [],
        "read_only_fields": [
            "qorg_external_opportunity", "qorg_external_person", "job_title",
            "applicant_name", "email_id", "phone_number", "status", "source",
        ],
    },
]
