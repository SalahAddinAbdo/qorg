from __future__ import annotations

MANAGED_VERSION = "4.0.0"


def page(label):
    return {"fieldtype": "Page Break", "label": label}


def section(label):
    return {"fieldtype": "Section Break", "label": label}


def column():
    return {"fieldtype": "Column Break"}


def field(fieldname, *, required=False, read_only=False, label=None):
    return {
        "fieldname": fieldname,
        "required": required,
        "read_only": read_only,
        "label": label,
    }


WEB_FORMS = [
    {
        "title": "External Profile",
        "route": "external-profile-form",
        "doc_type": "External Person",
        "allow_multiple": 0,
        "allow_edit": 1,
        "show_list": 1,
        "allow_print": 1,
        "introduction_text": "Create and maintain one professional profile for employment, volunteering, and internship applications.",
        "success_message": "Your professional profile has been saved successfully.",
        "submit_button_label": "Save Profile",
        "layout": [
            section("Identity and Contact"),
            field("full_name", required=True), field("name_in_arabic"),
            column(),
            field("first_name"), field("middle_name"), field("last_name"),
            section("Contact Details"),
            field("primary_email", required=True), field("mobile_no"), field("current_location"),
            column(),
            field("secondary_email"), field("alternative_mobile_no"), field("preferred_contact_method"), field("preferred_language"),
            page("Identity and Availability"),
            section("Identification"),
            field("identification_type"), field("identification_number"), field("identification_country"),
            column(),
            field("date_of_birth"), field("nationality"), field("marital_status"), field("gender"),
            section("Professional Availability"),
            field("professional_title", required=True), field("years_of_experience"), field("availability_status"),
            column(),
            field("image"), field("resume"),
            page("Professional Profile"),
            section("Professional Summary"),
            field("professional_summary", required=True), field("career_objective"), field("sectors_of_expertise"), field("key_achievements"),
            page("Education and Experience"),
            section("Education"), field("education"),
            section("Work Experience"), field("experience"),
            page("Skills and Development"),
            section("Skills"), field("skills"),
            section("Languages"), field("languages"),
            section("Training and Certifications"), field("training"),
            section("Volunteering Experience"), field("volunteer_experience"),
            page("References and Consent"),
            section("Professional References"), field("references"),
            section("Professional Links"), field("portfolio_url"), field("linkedin_url"),
            section("Consent"), field("privacy_consent", required=True),
        ],
    },
    {
        "title": "Participation Application",
        "route": "participation-application",
        "doc_type": "Participation Application",
        "allow_multiple": 1,
        "allow_edit": 1,
        "show_list": 1,
        "allow_print": 1,
        "introduction_text": "Apply using your saved external profile.",
        "success_message": "Your participation application has been submitted successfully.",
        "submit_button_label": "Submit Application",
        "layout": [
            section("Opportunity and Profile"),
            field("opportunity", required=True, read_only=True), field("external_person", required=True, read_only=True),
            column(),
            field("participation_type", required=True, read_only=True), field("application_date", required=True, read_only=True), field("status", required=True, read_only=True),
            section("Availability"),
            field("available_from"), field("available_to"), field("hours_per_week"),
            section("Application Details"),
            field("motivation", required=True), field("relevant_experience"), field("accommodation_needs"),
            section("Profile Confirmation"),
            field("profile_review_confirmed", required=True),
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
        "submit_button_label": "Submit Application",
        "layout": [
            section("Opportunity and Profile"),
            field("qorg_external_opportunity", read_only=True), field("qorg_external_person", read_only=True),
            column(),
            field("job_title", read_only=True), field("status", read_only=True), field("source", read_only=True),
            section("Applicant Details"),
            field("applicant_name", read_only=True), field("email_id", read_only=True), field("phone_number", read_only=True),
            section("Application"),
            field("cover_letter"), field("resume_attachment"), field("resume"),
        ],
    },
]
