from __future__ import annotations
import frappe
from frappe import _
from frappe.utils import add_days, cint, flt, getdate, today
from .settings import get_settings

def _empty(doc, field): return doc.meta.has_field(field) and doc.get(field) in (None, "", 0)
def _set_default(doc, field, value):
    if _empty(doc,field) and value not in (None,""): doc.set(field,value)

def apply_job_opening_defaults(doc, method=None):
    s=get_settings()
    _set_default(doc,"qorg_screening_weight",s.default_screening_weight)
    _set_default(doc,"qorg_assessment_weight",s.default_assessment_weight)
    for row in doc.get("qorg_screening_template") or []:
        _set_default(row,"maximum_score",100)
    for row in doc.get("qorg_assessment_plan") or []:
        _set_default(row,"passing_score",s.default_stage_passing_score)
        _set_default(row,"default_mode",s.default_interview_mode)
        _set_default(row,"duration_minutes",s.default_interview_duration)

def apply_interview_type_defaults(doc, method=None):
    s=get_settings()
    for row in doc.get("qorg_evaluation_criteria") or []:
        _set_default(row,"passing_score",s.default_criterion_passing_score)

def apply_interview_defaults(doc, method=None):
    s=get_settings()
    _set_default(doc,"qorg_interview_mode",s.default_interview_mode)
    _set_default(doc,"qorg_duration_minutes",s.default_interview_duration)
    _set_default(doc,"qorg_required_feedback_count",s.default_required_feedback_count)

def apply_job_offer_defaults(doc, method=None):
    s=get_settings()
    if doc.meta.has_field("qorg_valid_until") and not doc.get("qorg_valid_until"):
        base=doc.get("offer_date") or today();doc.qorg_valid_until=add_days(base,cint(s.default_offer_validity_days))
    if not cint(s.allow_multiple_active_offers) and doc.get("qorg_job_applicant"):
        applicant=frappe.get_doc("Job Applicant",doc.qorg_job_applicant)
        opening=applicant.get("job_title") or applicant.get("job_opening")
        if opening:
            applicants=frappe.get_all("Job Applicant",filters={"job_title":opening},pluck="name")
            existing=frappe.db.get_value("Job Offer",{"qorg_job_applicant":["in",applicants],"qorg_response_status":["not in",["Rejected","Expired","Withdrawn"]],"name":["!=",doc.name or ""]},"name")
            if existing: frappe.throw(_("An active offer already exists for this Job Opening: {0}").format(existing))

def validate_job_applicant_policy(doc, method=None):
    s=get_settings();decision=doc.get("qorg_final_decision")
    if decision in {"Selected","Reserve / Waitlisted"}:
        priority=cint(doc.get("qorg_selection_priority"))
        if priority<1 or priority>cint(s.candidate_priority_limit): frappe.throw(_("Selection Priority must be between 1 and {0}.").format(s.candidate_priority_limit))
        if cint(s.require_unique_priority):
            opening=doc.get("job_title") or doc.get("job_opening")
            duplicate=frappe.db.get_value("Job Applicant",{"job_title":opening,"qorg_selection_priority":priority,"qorg_final_decision":["in",["Selected","Reserve / Waitlisted"]],"name":["!=",doc.name or ""]},"name") if opening else None
            if duplicate: frappe.throw(_("Selection Priority {0} is already assigned to {1}.").format(priority,duplicate))
    if decision=="Rejected" and cint(s.require_rejection_reason) and not (doc.get("qorg_decision_rationale") or "").strip(): frappe.throw(_("Rejection reason is required."))
    if decision and cint(s.require_decision_rationale) and not (doc.get("qorg_decision_rationale") or "").strip(): frappe.throw(_("Evidence-based decision rationale is required."))
    if cint(s.lock_decision_after_offer) and not doc.is_new() and doc.has_value_changed("qorg_final_decision"):
        if frappe.db.exists("Job Offer",{"qorg_job_applicant":doc.name}): frappe.throw(_("Final decision is locked because a Job Offer exists. Use the protected reopen action."))

def validate_feedback_policy(doc, method=None):
    s=get_settings()
    if cint(s.require_evidence_notes) and doc.docstatus in (0,1):
        missing=[r.idx for r in doc.get("qorg_criterion_scores") or [] if not (r.evidence_notes or "").strip()]
        if missing: frappe.throw(_("Evidence Notes are required for criterion rows: {0}.").format(", ".join(map(str,missing))))

def apply_onboarding_defaults(doc, method=None):
    s=get_settings()
    if doc.meta.has_field("expected_end_date") and not doc.get("expected_end_date"):
        start=doc.get("boarding_begins_on") or doc.get("start_date") or today();doc.expected_end_date=add_days(start,cint(s.default_onboarding_duration_days))
    for row in doc.get("activities") or []:
        if cint(s.require_mandatory_activity_evidence) and row.get("qorg_is_mandatory"): row.qorg_requires_evidence=1
