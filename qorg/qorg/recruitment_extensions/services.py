from __future__ import annotations
import frappe
from frappe import _
from frappe.utils import getdate, flt, cint, now_datetime, today
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


RECRUITMENT_CONTEXT_FIELDS = (
    "qorg_job_opening", "qorg_project", "qorg_branch", "qorg_cost_center",
    "qorg_funding_source", "qorg_funding_end_date",
    "qorg_expected_contract_duration_months", "qorg_expected_joining_date",
)

def copy_recruitment_context(source, target):
    for field in RECRUITMENT_CONTEXT_FIELDS:
        if target.meta.has_field(field) and source.meta.has_field(field) and not target.get(field) and source.get(field) not in (None, ""):
            target.set(field, source.get(field))

def validate_funding_and_timeline(doc):
    from .settings import get_settings
    settings = get_settings()
    source = doc.get("qorg_funding_source")
    if getattr(settings, "require_funding_source", 0) and not source:
        frappe.throw(_("Funding Source is required."))
    if source == "Project Budget" and getattr(settings, "require_project_for_project_funding", 1) and not doc.get("qorg_project"):
        frappe.throw(_("Project is required for project-funded positions."))
    if source in {"Grant / Donor Funding", "Shared Funding", "Other"} and not (doc.get("qorg_funding_details") or "").strip():
        frappe.throw(_("Funding Details are required for the selected Funding Source."))
    if doc.get("qorg_expected_joining_date") and doc.get("qorg_funding_end_date") and getdate(doc.qorg_expected_joining_date) > getdate(doc.qorg_funding_end_date):
        policy = getattr(settings, "contract_beyond_funding_policy", "Require Justification")
        justified = bool((doc.get("qorg_funding_exception_justification") or "").strip())
        if policy == "Prevent": frappe.throw(_("Expected Joining Date cannot be after the Funding End Date."))
        if policy == "Require Justification" and not justified: frappe.throw(_("Funding Exception Justification is required because the planned employment period exceeds the funding period."))
        if policy == "Warn": frappe.msgprint(_("The planned employment period exceeds the funding period."), indicator="orange")

def validate_recruitment_timeline(doc):
    from .settings import get_settings
    settings=get_settings()
    required=(("qorg_shortlisting_deadline","require_shortlisting_deadline"),("qorg_interview_start_date","require_interview_start_date"),("qorg_target_decision_date","require_target_decision_date"))
    for field,setting in required:
        if getattr(settings,setting,0) and not doc.get(field): frappe.throw(_("{0} is required.").format(doc.meta.get_label(field)))
    if not getattr(settings,"validate_recruitment_date_sequence",1): return
    sequence=[]
    for field in ("closes_on","qorg_shortlisting_deadline","qorg_interview_start_date","qorg_target_decision_date","qorg_offer_issue_target_date","qorg_expected_joining_date"):
        if doc.meta.has_field(field) and doc.get(field): sequence.append((field,getdate(doc.get(field))))
    for previous,current in zip(sequence,sequence[1:]):
        if current[1] < previous[1]: frappe.throw(_("{0} cannot be earlier than {1}.").format(doc.meta.get_label(current[0]),doc.meta.get_label(previous[0])))

def sync_opening_from_requisition(doc):
    if not doc.get("qorg_job_requisition") or not frappe.db.exists("Job Requisition",doc.qorg_job_requisition): return
    req=frappe.get_doc("Job Requisition",doc.qorg_job_requisition)
    mapping=("qorg_recruitment_need_type","qorg_project","qorg_branch","qorg_cost_center","qorg_funding_source","qorg_funding_end_date","qorg_expected_contract_duration_months","qorg_expected_joining_date","qorg_funding_details","qorg_funding_exception_justification")
    for field in mapping:
        if doc.meta.has_field(field) and not doc.get(field) and req.get(field) not in (None,""): doc.set(field,req.get(field))

def validate_job_requisition_extension(doc):
    validate_funding_and_timeline(doc)

def validate_job_opening_extension(doc):
    from .settings import get_settings
    sync_opening_from_requisition(doc); settings=get_settings()
    if not doc.get("qorg_vacancy_scope"): doc.qorg_vacancy_scope=getattr(settings,"default_vacancy_scope","Internal and External")
    if getattr(settings,"require_recruitment_coordinator",0) and not doc.get("qorg_recruitment_coordinator"): frappe.throw(_("Recruitment Coordinator is required."))
    if getattr(settings,"require_hiring_manager",0) and not doc.get("qorg_hiring_manager"): frappe.throw(_("Hiring Manager is required."))
    validate_funding_and_timeline(doc); validate_recruitment_timeline(doc)


def _opening_for_applicant(applicant):
    return applicant.get("qorg_job_opening") or applicant.get("job_title") or applicant.get("job_opening")

def _assessment_plan(opening_name):
    if not opening_name or not frappe.db.exists("Job Opening", opening_name): return []
    return frappe.get_all("Recruitment Assessment Stage", filters={"parent":opening_name,"parenttype":"Job Opening","parentfield":"qorg_assessment_plan"}, fields=["name","sequence","stage_name","assessment_type","interview_type","weight","passing_score","is_mandatory","default_mode","duration_minutes","allow_retry","maximum_attempts","retry_requires_approval","retry_approval_role","retry_instructions"], order_by="sequence asc, idx asc")

def configure_interview(doc):
    if not doc.get("job_applicant"): return
    applicant=frappe.get_doc("Job Applicant",doc.job_applicant); copy_context(applicant,doc)
    opening=_opening_for_applicant(applicant); _set_if_empty(doc,"qorg_job_opening",opening)
    plan=_assessment_plan(opening)
    stage=None
    if doc.get("qorg_stage_sequence"): stage=next((r for r in plan if cint(r.sequence)==cint(doc.qorg_stage_sequence)),None)
    if not stage:
        itype=doc.get("interview_type") or doc.get("interview_round")
        matches=[r for r in plan if r.interview_type==itype]
        if len(matches)==1:stage=matches[0]
    if not stage:return
    mapping={"qorg_stage_sequence":stage.sequence,"qorg_stage_name":stage.stage_name,"qorg_stage_weight":stage.weight,"qorg_passing_score":stage.passing_score,"qorg_is_mandatory_stage":stage.is_mandatory,"qorg_interview_mode":stage.default_mode,"qorg_duration_minutes":stage.duration_minutes,"qorg_allow_retry":stage.allow_retry,"qorg_maximum_attempts":max(cint(stage.maximum_attempts),1),"qorg_retry_requires_approval":stage.retry_requires_approval,"qorg_retry_approval_role":stage.retry_approval_role}
    for field,value in mapping.items():_set_if_empty(doc,field,value)
    if not doc.get("qorg_attempt_number"):doc.qorg_attempt_number=1

def _stage_attempts(applicant_name, opening_name, stage):
    filters={"job_applicant":applicant_name,"qorg_job_opening":opening_name,"qorg_stage_sequence":stage.sequence}
    fields=["name","qorg_attempt_number","qorg_panel_completion_status","qorg_assessment_result","qorg_final_score","status","modified"]
    return frappe.get_all("Interview",filters=filters,fields=fields,order_by="qorg_attempt_number asc, creation asc")

def stage_progress(applicant_name):
    applicant=frappe.get_doc("Job Applicant",applicant_name);opening=_opening_for_applicant(applicant);plan=_assessment_plan(opening)
    progress=[]
    for stage in plan:
        attempts=[r for r in _stage_attempts(applicant_name,opening,stage) if r.status not in {"Cancelled","Canceled"}]
        effective=attempts[-1] if attempts else None
        progress.append(frappe._dict({"stage":stage,"attempts":attempts,"effective":effective,"completed":bool(effective and effective.qorg_panel_completion_status=="Complete"),"passed":bool(effective and effective.qorg_assessment_result=="Passed"),"failed":bool(effective and effective.qorg_assessment_result=="Failed"),"attempts_used":len(attempts),"attempts_allowed":max(cint(stage.maximum_attempts),1)}))
    return opening,progress

def recalculate_applicant(applicant_name):
    doc=frappe.get_doc("Job Applicant",applicant_name);opening,progress=stage_progress(applicant_name)
    screening=flt(doc.get("qorg_screening_score"));sw=flt(frappe.db.get_value("Job Opening",opening,"qorg_screening_weight") or 20) if opening else 20;aw=flt(frappe.db.get_value("Job Opening",opening,"qorg_assessment_weight") or 80) if opening else 80
    completed=[p for p in progress if p.completed];failed=[p for p in completed if p.failed and cint(p.stage.is_mandatory)];completed_weight=sum(flt(p.stage.weight) for p in completed)
    assessment=flt(sum(flt(p.effective.qorg_final_score)*flt(p.stage.weight) for p in completed)/completed_weight,2) if completed_weight else 0
    overall=flt(screening*sw/100+assessment*aw/100,2)
    values={"qorg_assessment_score":assessment,"qorg_effective_stage_score":assessment,"qorg_overall_score":overall,"qorg_required_stages":len(progress),"qorg_completed_stages":len(completed),"qorg_failed_stages":len(failed),"qorg_remaining_stages":max(len(progress)-len(completed),0),"qorg_completed_stage_weight":completed_weight}
    frappe.db.set_value("Job Applicant",applicant_name,values,update_modified=False);recalculate_ranking(opening);return values

def recalculate_ranking(opening_name):
    if not opening_name:return []
    fields=["name","qorg_overall_score","qorg_final_decision","qorg_selection_status"]
    candidates=frappe.get_all("Job Applicant",filters={"qorg_job_opening":opening_name},fields=fields,order_by="qorg_overall_score desc, creation asc") if frappe.get_meta("Job Applicant").has_field("qorg_job_opening") else frappe.get_all("Job Applicant",filters={"job_title":opening_name},fields=fields,order_by="qorg_overall_score desc, creation asc")
    rank=0
    for row in candidates:
        if row.qorg_final_decision in {"Withdrawn","Disqualified","Cancelled"}:continue
        rank+=1;frappe.db.set_value("Job Applicant",row.name,"qorg_rank",rank,update_modified=False)
    return candidates

def retry_eligibility(interview_name,user=None):
    interview=frappe.get_doc("Interview",interview_name);user=user or frappe.session.user
    if interview.get("qorg_panel_completion_status")!="Complete" or interview.get("qorg_assessment_result")!="Failed":return {"allowed":False,"reason":_("Only a completed failed interview can be retried.")}
    if not cint(interview.get("qorg_allow_retry")):return {"allowed":False,"reason":_("Retry is disabled for this assessment stage.")}
    maximum=max(cint(interview.get("qorg_maximum_attempts")),1); current=max(cint(interview.get("qorg_attempt_number")),1)
    if current>=maximum:return {"allowed":False,"reason":_("Maximum attempts have been reached.")}
    existing=frappe.db.get_value("Interview",{"qorg_previous_interview":interview.name,"status":["not in",["Cancelled","Canceled"]]},"name")
    if existing:return {"allowed":True,"existing":existing,"reason":_("A retry interview already exists.")}
    if cint(interview.get("qorg_retry_requires_approval")):
        role=interview.get("qorg_retry_approval_role") or "HR Manager"
        if role not in frappe.get_roles(user) and user!="Administrator":return {"allowed":False,"reason":_("Retry approval requires role {0}.").format(role)}
    return {"allowed":True,"existing":None,"reason":""}
