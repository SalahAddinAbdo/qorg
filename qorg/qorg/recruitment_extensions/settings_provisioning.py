import json
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

INITIAL_DEFAULTS = {
    "qorg_default_screening_weight": 20,
    "qorg_default_assessment_weight": 80,
    "qorg_default_criterion_passing_score": 60,
    "qorg_default_stage_passing_score": 60,
    "qorg_default_interview_mode": "In Person",
    "qorg_default_interview_duration": 60,
    "qorg_default_required_feedback_count": 1,
    "qorg_require_evidence_notes": 1,
    "qorg_default_offer_validity_days": 7,
    "qorg_automatically_expire_offers": 1,
    "qorg_allow_multiple_active_offers": 0,
    "qorg_candidate_priority_limit": 3,
    "qorg_require_unique_priority": 1,
    "qorg_require_rejection_reason": 1,
    "qorg_require_decision_rationale": 1,
    "qorg_lock_decision_after_offer": 1,
    "qorg_enable_applicant_notifications": 1,
    "qorg_enable_interviewer_notifications": 1,
    "qorg_enable_recruitment_team_notifications": 1,
    "qorg_send_confirmation_copy_sender": 1,
    "qorg_require_recipient_confirmation": 1,
    "qorg_use_company_branding": 1,
    "qorg_default_onboarding_duration_days": 30,
    "qorg_require_mandatory_onboarding": 1,
    "qorg_require_mandatory_activity_evidence": 0,
    "qorg_require_activity_verification": 1,
    "qorg_allow_assigned_user_reopen": 0,
}

def _load(name):
    path = frappe.get_app_path("qorg", "qorg", "recruitment_extensions", "data", name)
    return json.load(open(path, encoding="utf-8"))

def _provision_fields():
    fields = _load("hr_settings_custom_fields.json")
    create_custom_fields({"HR Settings": fields}, update=True)

    grouped = {}
    for row in _load("recruitment_settings_operational_fields.json"):
        row = dict(row)
        doctype = row.pop("dt")
        if frappe.db.exists("DocType", doctype):
            grouped.setdefault(doctype, []).append(row)
    if grouped:
        create_custom_fields(grouped, update=True)

def _initialize_defaults_once():
    doc = frappe.get_single("HR Settings")
    if doc.get("qorg_recruitment_settings_initialized"):
        return
    for fieldname, value in INITIAL_DEFAULTS.items():
        if doc.meta.has_field(fieldname):
            doc.set(fieldname, value)
    doc.qorg_recruitment_settings_initialized = 1
    doc.save(ignore_permissions=True)

def provision_recruitment_settings():
    if not frappe.db.exists("DocType", "HR Settings"):
        return
    _provision_fields()
    frappe.clear_cache(doctype="HR Settings")
    _initialize_defaults_once()
    frappe.clear_cache(doctype="HR Settings")
