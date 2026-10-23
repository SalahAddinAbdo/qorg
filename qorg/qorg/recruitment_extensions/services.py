from __future__ import annotations
import frappe
from frappe import _
from frappe.utils import flt, cint, now_datetime, today
from .constants import FINAL_DECISIONS, ACTIVE_SELECTION_DECISIONS, TERMINAL_OFFER_RESPONSES


def _meta_has(dt, field):
    return bool(frappe.db.exists("DocType", dt) and frappe.get_meta(dt).has_field(field))

def _set_if_empty(doc, field, value):
    if value not in (None, "") and hasattr(doc, field) and not doc.get(field): doc.set(field, value)

def copy_context(source, target):
    for field in ("qorg_project", "qorg_branch"):
        _set_if_empty(target, field, source.get(field))

def linked_job_opening(applicant):
    return applicant.get("job_title") or applicant.get("job_opening")

def validate_weights(doc):
    screening=flt(doc.get("qorg_screening_weight")); assessment=flt(doc.get("qorg_assessment_weight"))
    if abs((screening+assessment)-100)>0.01: frappe.throw(_("Screening and assessment weights must total 100%."))
    stages=doc.get("qorg_assessment_plan") or []
    if stages:
        total=sum(flt(r.weight) for r in stages)
        if abs(total-100)>0.01: frappe.throw(_("Assessment stage weights must total 100%. Current total: {0}%").format(total))
        seq=set()
        for row in stages:
            if cint(row.sequence) in seq: frappe.throw(_("Assessment stage sequence must be unique."))
            seq.add(cint(row.sequence))
            if not row.interview_type: frappe.throw(_("Interview Type is required in every assessment stage."))
            if flt(row.passing_score)<0 or flt(row.passing_score)>100: frappe.throw(_("Passing score must be between 0 and 100."))

def validate_interview_type(doc):
    rows=doc.get("qorg_evaluation_criteria") or []
    if rows:
        total=sum(flt(r.weight) for r in rows)
        if abs(total-100)>0.01: frappe.throw(_("Evaluation criterion weights must total 100%. Current total: {0}%").format(total))
        for r in rows:
            if not r.question_task: frappe.throw(_("Question / Task is required for every evaluation criterion."))
            if flt(r.passing_score)<0 or flt(r.passing_score)>100: frappe.throw(_("Criterion passing score must be between 0 and 100."))

def sync_screening_criteria(applicant, force=False):
    opening=linked_job_opening(applicant)
    if not opening or not frappe.db.exists("Job Opening", opening): return
    if applicant.get("qorg_screening_criteria") and not force: return
    rows=frappe.get_all("Recruitment Screening Template Criterion", filters={"parent":opening,"parenttype":"Job Opening","parentfield":"qorg_screening_template"}, fields=["sequence","criterion","criterion_type","is_mandatory","maximum_score","expected_evidence"], order_by="sequence asc")
    applicant.set("qorg_screening_criteria", [])
    for r in rows: applicant.append("qorg_screening_criteria", r)

def sync_context(doc, source=None):
    if source: copy_context(source, doc)

def configure_interview(doc):
    if not doc.get("job_applicant"): return
    applicant=frappe.get_doc("Job Applicant", doc.job_applicant)
    copy_context(applicant, doc)
    opening=linked_job_opening(applicant)
    itype=doc.get("interview_type") or doc.get("interview_round")
    if not opening or not itype: return
    stages=frappe.get_all("Recruitment Assessment Stage", filters={"parent":opening,"parenttype":"Job Opening","parentfield":"qorg_assessment_plan","interview_type":itype}, fields=["sequence","stage_name","assessment_type","weight","passing_score","is_mandatory","default_mode","duration_minutes","maximum_attempts"], order_by="sequence asc", limit=1)
    if stages:
        s=stages[0]
        mapping={"qorg_stage_sequence":s.sequence,"qorg_stage_name":s.stage_name,"qorg_assessment_type":s.assessment_type,"qorg_stage_weight":s.weight,"qorg_passing_score":s.passing_score,"qorg_is_mandatory_stage":s.is_mandatory,"qorg_interview_mode":s.default_mode,"qorg_duration_minutes":s.duration_minutes,"qorg_maximum_attempts":s.maximum_attempts}
        for k,v in mapping.items(): _set_if_empty(doc,k,v)

def copy_feedback_criteria(feedback):
    if feedback.get("qorg_criterion_scores"): return
    interview=frappe.get_doc("Interview", feedback.interview)
    copy_context(interview, feedback)
    itype=interview.get("interview_type") or interview.get("interview_round")
    if not itype: return
    rows=frappe.get_all("Interview Evaluation Criterion", filters={"parent":itype,"parenttype":"Interview Type","parentfield":"qorg_evaluation_criteria"}, fields=["name","sequence","competency_area","question_task","weight","passing_score","is_mandatory"], order_by="sequence asc")
    for r in rows:
        feedback.append("qorg_criterion_scores", {"criterion_reference":r.name,"sequence":r.sequence,"competency_area":r.competency_area,"question_task":r.question_task,"weight":r.weight,"passing_score":r.passing_score,"is_mandatory":r.is_mandatory})

def calculate_feedback(feedback, require_evidence=True):
    rows=feedback.get("qorg_criterion_scores") or []
    if not rows: return 0
    total_weight=sum(flt(r.weight) for r in rows)
    if abs(total_weight-100)>0.01: frappe.throw(_("Criterion weights must total 100%."))
    score=0; failed=[]
    for r in rows:
        pct=flt(r.score_percent)
        if pct<0 or pct>100: frappe.throw(_("Score must be between 0 and 100."))
        if require_evidence and not (r.evidence_notes or "").strip(): frappe.throw(_("Evidence Notes are required for criterion {0}.").format(r.competency_area or r.question_task))
        r.weighted_score=flt(pct*flt(r.weight)/100,2)
        r.result="Passed" if pct>=flt(r.passing_score) else "Failed"
        if cint(r.is_mandatory) and r.result=="Failed": failed.append(r.competency_area or r.question_task)
        score+=r.weighted_score
    feedback.qorg_weighted_score=flt(score,2); feedback.qorg_failed_mandatory_criteria=", ".join(failed)
    return feedback.qorg_weighted_score

def recalculate_interview(interview_name):
    interview=frappe.get_doc("Interview", interview_name)
    names=frappe.get_all("Interview Feedback", filters={"interview":interview_name,"docstatus":1}, pluck="name")
    scores=[flt(frappe.db.get_value("Interview Feedback", n, "qorg_weighted_score")) for n in names]
    submitted=len(scores); required=max(cint(interview.get("qorg_required_feedback_count") or 1),1)
    final=flt(sum(scores)/len(scores),2) if scores else 0
    status="Complete" if submitted>=required else ("Awaiting Feedback" if submitted else "Not Started")
    result="Passed" if status=="Complete" and final>=flt(interview.get("qorg_passing_score")) else ("Failed" if status=="Complete" else "Pending")
    frappe.db.set_value("Interview", interview_name, {"qorg_submitted_feedback_count":submitted,"qorg_missing_feedback_count":max(required-submitted,0),"qorg_panel_completion_status":status,"qorg_final_score":final,"qorg_assessment_result":result}, update_modified=False)
    if interview.job_applicant: recalculate_applicant(interview.job_applicant)
    return final

def _latest_valid_interviews(applicant_name):
    fields=["name","interview_type","interview_round","qorg_stage_weight","qorg_passing_score","qorg_is_mandatory_stage","qorg_final_score","qorg_assessment_result","qorg_panel_completion_status","qorg_stage_sequence","qorg_attempt_number","status"]
    fields=[f for f in fields if _meta_has("Interview",f)]
    rows=frappe.get_all("Interview",filters={"job_applicant":applicant_name},fields=fields,order_by="creation asc")
    latest={}
    for r in rows:
        if r.get("status") in {"Cancelled","Canceled"}: continue
        key=r.get("interview_type") or r.get("interview_round") or r.get("qorg_stage_sequence")
        if key: latest[key]=r
    return list(latest.values())

def recalculate_applicant(applicant_name):
    doc=frappe.get_doc("Job Applicant",applicant_name)
    screening=flt(doc.get("qorg_screening_score")); opening=linked_job_opening(doc)
    sw=flt(frappe.db.get_value("Job Opening",opening,"qorg_screening_weight") or 20) if opening else 20
    aw=flt(frappe.db.get_value("Job Opening",opening,"qorg_assessment_weight") or 80) if opening else 80
    stages=_latest_valid_interviews(applicant_name)
    completed=[r for r in stages if r.get("qorg_panel_completion_status")=="Complete"]
    failed=[r for r in completed if r.get("qorg_assessment_result")=="Failed" and cint(r.get("qorg_is_mandatory_stage"))]
    required=len(stages); done=len(completed); completed_weight=sum(flt(r.get("qorg_stage_weight")) for r in completed)
    assessment=flt(sum(flt(r.get("qorg_final_score"))*flt(r.get("qorg_stage_weight")) for r in completed)/completed_weight,2) if completed_weight else 0
    overall=flt(screening*sw/100 + assessment*aw/100,2)
    values={"qorg_assessment_score":assessment,"qorg_overall_score":overall,"qorg_required_stages":required,"qorg_completed_stages":done,"qorg_failed_stages":len(failed),"qorg_remaining_stages":max(required-done,0),"qorg_completed_stage_weight":completed_weight}
    frappe.db.set_value("Job Applicant",applicant_name,values,update_modified=False)
    return values

def validate_final_decision(doc):
    decision=doc.get("qorg_final_decision")
    if decision in ACTIVE_SELECTION_DECISIONS:
        if cint(doc.get("qorg_remaining_stages")) or cint(doc.get("qorg_failed_stages")): frappe.throw(_("Mandatory assessments must be completed and passed before selecting or waitlisting the applicant."))
        if not cint(doc.get("qorg_selection_priority")): frappe.throw(_("Selection Priority is required."))
        if not (doc.get("qorg_decision_rationale") or "").strip(): frappe.throw(_("Evidence-based decision rationale is required."))

def next_offer_candidate(job_opening):
    rows=frappe.get_all("Job Applicant",filters={"job_title":job_opening,"qorg_final_decision":["in",list(ACTIVE_SELECTION_DECISIONS)],"qorg_selection_status":["not in",["Offer Accepted","Employee Created"]]},fields=["name","qorg_selection_priority","qorg_selection_status"],order_by="qorg_selection_priority asc")
    return rows[0].name if rows else None

def propagate_context(source, target): copy_context(source,target)
