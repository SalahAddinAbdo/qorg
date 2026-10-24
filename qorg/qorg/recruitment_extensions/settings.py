from __future__ import annotations
import frappe
from frappe import _
from frappe.utils import cint, flt

DEFAULTS = {
    "require_funding_source": 0,
    "require_project_for_project_funding": 1,
    "auto_fetch_cost_center": 1,
    "contract_beyond_funding_policy": "Require Justification",
    "require_funding_exception_justification": 1,
    "validate_recruitment_date_sequence": 1,
    "require_shortlisting_deadline": 0,
    "require_interview_start_date": 0,
    "require_target_decision_date": 0,
    "default_vacancy_scope": "Internal and External",
    "require_recruitment_coordinator": 0,
    "require_hiring_manager": 0,
    "default_screening_weight": 20,
    "default_assessment_weight": 80,
    "default_criterion_passing_score": 60,
    "default_stage_passing_score": 60,
    "default_interview_mode": "In Person",
    "default_interview_duration": 60,
    "default_required_feedback_count": 1,
    "require_evidence_notes": 1,
    "default_offer_validity_days": 7,
    "automatically_expire_offers": 1,
    "allow_multiple_active_offers": 0,
    "candidate_priority_limit": 3,
    "require_unique_priority": 1,
    "require_rejection_reason": 1,
    "require_decision_rationale": 1,
    "lock_decision_after_offer": 1,
    "enable_applicant_notifications": 1,
    "enable_interviewer_notifications": 1,
    "enable_recruitment_team_notifications": 1,
    "send_confirmation_copy_sender": 1,
    "require_recipient_confirmation": 1,
    "use_company_branding": 1,
    "default_onboarding_duration_days": 30,
    "require_mandatory_onboarding": 1,
    "require_mandatory_activity_evidence": 0,
    "require_activity_verification": 1,
    "allow_assigned_user_reopen": 0,
}

def _field(key): return f"qorg_{key}"

def get_settings():
    result=dict(DEFAULTS)
    if not frappe.db.exists("DocType","HR Settings"): return frappe._dict(result)
    doc=frappe.get_single("HR Settings")
    for key, default in DEFAULTS.items():
        field=_field(key)
        value=doc.get(field) if doc.meta.has_field(field) else None
        if value not in (None, ""): result[key]=value
    result["default_cc_users"]=[r.user for r in (doc.get("qorg_default_recruitment_cc_users") or []) if r.user]
    result["default_additional_users"]=[r.user for r in (doc.get("qorg_default_recruitment_additional_users") or []) if r.user]
    return frappe._dict(result)

def validate_hr_settings(doc, method=None):
    total=flt(doc.qorg_default_screening_weight)+flt(doc.qorg_default_assessment_weight)
    if abs(total-100)>0.01: frappe.throw(_("Default Screening and Assessment weights must total exactly 100%. Current total: {0}%.").format(total))
    percent_fields=("qorg_default_screening_weight","qorg_default_assessment_weight","qorg_default_criterion_passing_score","qorg_default_stage_passing_score")
    for field in percent_fields:
        value=flt(doc.get(field))
        if value<0 or value>100: frappe.throw(_("{0} must be between 0 and 100%.").format(doc.meta.get_label(field)))
    positive=("qorg_default_interview_duration","qorg_default_required_feedback_count","qorg_default_offer_validity_days","qorg_candidate_priority_limit","qorg_default_onboarding_duration_days")
    for field in positive:
        if cint(doc.get(field))<1: frappe.throw(_("{0} must be at least 1.").format(doc.meta.get_label(field)))
