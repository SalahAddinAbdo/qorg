from __future__ import annotations
import frappe
from frappe.utils import add_days, flt, getdate, now, today
from qorg.qorg.people_and_opportunities.settings import require_feature
from qorg.qorg.recruitment_extensions.settings import get_settings
FINAL_DECISIONS={"Selected","Reserve / Waitlisted","Rejected","Withdrawn","No Show","Disqualified","Cancelled"}
ACTIVE_OFFER_STATES={"Draft","Issued","Accepted"}
TERMINAL_OFFER_STATES={"Rejected","Expired","Withdrawn"}

def interview_type_field():
    meta=frappe.get_meta("Interview")
    if meta.has_field("interview_type"):
        return "interview_type"
    if meta.has_field("interview_round"):
        return "interview_round"
    frappe.throw("Interview has no Interview Type field. Complete the HRMS v16 migration first.")

def get_interview_type(interview_or_doc):
    fieldname=interview_type_field()
    if isinstance(interview_or_doc,str):
        return frappe.db.get_value("Interview",interview_or_doc,fieldname)
    return interview_or_doc.get(fieldname)

def company_of_applicant(doc):
    opening=getattr(doc,"job_title",None)
    return frappe.db.get_value("Job Opening",opening,"company") if opening else None

def validate_assessment_plan(doc):
    sw,iw=flt(doc.qorg_screening_weight),flt(doc.qorg_interview_weight)
    if abs(sw+iw-100)>0.01:frappe.throw("Screening Weight and Interview Weight must total 100%.")
    seen=set();stage_weight=0
    for row in doc.qorg_assessment_plan or []:
        if row.sequence in seen:frappe.throw("Assessment stage sequence must be unique.")
        seen.add(row.sequence);stage_weight+=flt(row.weight)
        if row.assessment_type in {"Structured Interview","Technical Interview"} and not row.interview_type:frappe.throw("Interview Type is required for interview stages.")
        if not 0<=flt(row.passing_score)<=100:frappe.throw("Stage Passing Score must be between 0 and 100.")
    if doc.qorg_assessment_plan and abs(stage_weight-100)>0.01:frappe.throw("Assessment stage weights must total 100%.")

def validate_interview_type(doc):
    total=0;seen=set()
    for row in doc.qorg_evaluation_criteria or []:
        if row.sequence in seen:frappe.throw("Evaluation criterion sequence must be unique.")
        seen.add(row.sequence);total+=flt(row.weight)
        if flt(row.maximum_score)<=0:frappe.throw("Maximum Score must be greater than zero.")
        if flt(row.minimum_score)>flt(row.maximum_score):frappe.throw("Minimum Score cannot exceed Maximum Score.")
        if row.is_mandatory and not (row.behavioral_anchor_low and row.behavioral_anchor_mid and row.behavioral_anchor_high):frappe.throw(f"Behavioral anchors are required for mandatory criterion: {row.competency}")
    if doc.qorg_evaluation_criteria and abs(total-100)>0.01:frappe.throw("Evaluation criterion weights must total 100%.")

def validate_job_applicant(doc):
    company=company_of_applicant(doc);require_feature("extended_recruitment",company)
    if doc.qorg_external_opportunity:
        linked=frappe.db.get_value("External Opportunity",doc.qorg_external_opportunity,"job_opening")
        if linked and doc.job_title and linked!=doc.job_title:frappe.throw("External Opportunity does not match Job Opening.")
    if doc.qorg_external_person and doc.qorg_external_opportunity:
        other=frappe.db.get_value("Job Applicant",{"qorg_external_person":doc.qorg_external_person,"qorg_external_opportunity":doc.qorg_external_opportunity,"name":["!=",doc.name or ""],"status":["not in",["Rejected","Withdrawn"]]},"name")
        if other:frappe.throw(f"An active application already exists: {other}")
    total=maximum=0.0;mandatory_failed=False
    for row in doc.qorg_screening_criteria or []:
        if flt(row.maximum_score)<0 or flt(row.score)<0 or flt(row.score)>flt(row.maximum_score):frappe.throw(f"Invalid screening score for {row.criterion}.")
        total+=flt(row.score);maximum+=flt(row.maximum_score)
        if row.is_mandatory and row.result=="Not Met":mandatory_failed=True
    doc.qorg_screening_score=round(total*100/maximum,2) if maximum else 0
    if mandatory_failed and doc.qorg_screening_status in {"Eligible","Shortlisted"}:frappe.throw("Mandatory screening criteria are not met.")

def apply_interview_stage_defaults(doc):
    if not doc.job_applicant or not get_interview_type(doc):return
    opening=frappe.db.get_value("Job Applicant",doc.job_applicant,"job_title")
    stage=frappe.db.get_value("Recruitment Assessment Stage",{"parent":opening,"parenttype":"Job Opening","parentfield":"qorg_assessment_plan","interview_type":get_interview_type(doc)},["sequence","assessment_type","passing_score","default_mode"],as_dict=True)
    if stage:
        doc.qorg_stage_sequence=stage.sequence;doc.qorg_assessment_type=stage.assessment_type;doc.qorg_passing_score=stage.passing_score
        if not doc.qorg_mode:doc.qorg_mode=stage.default_mode

def validate_interview(doc):
    apply_interview_stage_defaults(doc)
    if doc.qorg_mode in {"In Person","Hybrid"} and not doc.qorg_venue:frappe.throw("Venue is required for in-person or hybrid interviews.")
    if doc.qorg_mode in {"Online","Hybrid"} and not doc.qorg_meeting_url:frappe.throw("Meeting URL is required for online or hybrid interviews.")
    if doc.qorg_attendance_status=="Attended" and doc.status=="Scheduled":frappe.throw("End or complete the interview before marking attendance as Attended.")

def populate_feedback_criteria(doc):
    if not doc.interview or doc.qorg_criterion_scores:return
    type_name=get_interview_type(doc.interview)
    rows=frappe.get_all("Interview Evaluation Criterion",filters={"parent":type_name,"parenttype":"Interview Type","parentfield":"qorg_evaluation_criteria"},fields=["name","competency","question","weight","maximum_score"],order_by="idx")
    if not rows:frappe.throw("The Interview Type has no structured evaluation criteria.")
    for row in rows:doc.append("qorg_criterion_scores",{"criterion_reference":row.name,"competency":row.competency,"question":row.question,"weight":row.weight,"maximum_score":row.maximum_score})

def validate_feedback(doc):
    populate_feedback_criteria(doc);weighted=weight_total=0.0
    interview=frappe.db.get_value("Interview",doc.interview,["qorg_attendance_status",interview_type_field()],as_dict=True)
    if interview and interview.qorg_attendance_status!="Attended":frappe.throw("Feedback can only be submitted for an attended interview.")
    for row in doc.qorg_criterion_scores or []:
        if flt(row.score)<0 or flt(row.score)>flt(row.maximum_score):frappe.throw(f"Score for {row.competency} must be between 0 and {row.maximum_score}.")
        if get_settings().require_evidence_notes and not row.evidence_notes:frappe.throw(f"Evidence Notes are required for {row.competency}.")
        weighted+=(flt(row.score)/flt(row.maximum_score))*flt(row.weight) if flt(row.maximum_score) else 0;weight_total+=flt(row.weight)
    doc.qorg_weighted_score=round(weighted*100/weight_total,2) if weight_total else 0

def update_interview_score(interview):
    scores=[flt(x) for x in frappe.get_all("Interview Feedback",filters={"interview":interview,"docstatus":1},pluck="qorg_weighted_score")]
    score=round(sum(scores)/len(scores),2) if scores else 0
    frappe.db.set_value("Interview",interview,"qorg_final_score",score,update_modified=False)

def mandatory_stage_status(applicant):
    opening=frappe.db.get_value("Job Applicant",applicant,"job_title")
    plan=frappe.get_all("Recruitment Assessment Stage",filters={"parent":opening,"parenttype":"Job Opening","parentfield":"qorg_assessment_plan","is_mandatory":1},fields=["stage_name","interview_type","passing_score","assessment_type","weight"],order_by="sequence")
    missing=[];failed=[];completed=[]
    for stage in plan:
        if not stage.interview_type:
            missing.append(stage.stage_name);continue
        row=frappe.db.get_value("Interview",{"job_applicant":applicant,interview_type_field():stage.interview_type},["name","qorg_attendance_status","qorg_final_score"],as_dict=True)
        if not row or row.qorg_attendance_status!="Attended":missing.append(stage.stage_name)
        elif flt(row.qorg_final_score)<flt(stage.passing_score):failed.append(stage.stage_name)
        else:completed.append(stage.stage_name)
    return missing,failed,completed

def interview_scores(applicant):
    opening=frappe.db.get_value("Job Applicant",applicant,"job_title")
    stages=frappe.get_all("Recruitment Assessment Stage",filters={"parent":opening,"parenttype":"Job Opening","parentfield":"qorg_assessment_plan"},fields=["stage_name","interview_type","weight","is_mandatory","passing_score"],order_by="sequence")
    weighted=weight_total=0.0;missing=[];failed=[]
    for stage in stages:
        if not stage.interview_type:
            if stage.is_mandatory:missing.append(stage.stage_name)
            continue
        row=frappe.db.get_value("Interview",{"job_applicant":applicant,interview_type_field():stage.interview_type},["name","qorg_attendance_status","qorg_final_score"],as_dict=True)
        if not row or row.qorg_attendance_status!="Attended":
            if stage.is_mandatory:missing.append(stage.stage_name)
            continue
        if flt(row.qorg_final_score)<flt(stage.passing_score) and stage.is_mandatory:failed.append(stage.stage_name)
        weighted+=flt(row.qorg_final_score)*flt(stage.weight);weight_total+=flt(stage.weight)
    return (round(weighted/weight_total,2) if weight_total else 0,missing,failed)

def overall_score(applicant,interview_score):
    values=frappe.db.get_value("Job Applicant",applicant,["qorg_screening_score","job_title"],as_dict=True) or {}
    weights=frappe.db.get_value("Job Opening",values.get("job_title"),["qorg_screening_weight","qorg_interview_weight"],as_dict=True) or {}
    sw,iw=flt(weights.get("qorg_screening_weight") or 20),flt(weights.get("qorg_interview_weight") or 80)
    return round((flt(values.get("qorg_screening_score"))*sw+flt(interview_score)*iw)/(sw+iw or 100),2)

def next_offer_candidate(opening,exclude=None):
    filters={"job_title":opening,"qorg_final_decision":["in",["Selected","Reserve / Waitlisted"]],"qorg_selection_status":["not in",["Offer Accepted","Appointment Issued","Employee Created","Closed"]]}
    if exclude:filters["name"]=["!=",exclude]
    rows=frappe.get_all("Job Applicant",filters=filters,fields=["name","qorg_selection_priority","qorg_overall_score"],order_by="qorg_selection_priority asc, qorg_overall_score desc, creation asc")
    for row in rows:
        active=frappe.db.exists("Job Offer",{"qorg_applicant":row.name,"qorg_response_status":["in",list(ACTIVE_OFFER_STATES)]})
        if not active:return row.name
    return None

def validate_job_offer(doc):
    applicant=doc.qorg_applicant or getattr(doc,"job_applicant",None)
    if not applicant:return
    info=frappe.db.get_value("Job Applicant",applicant,["qorg_final_decision","job_title","qorg_selection_priority"],as_dict=True)
    if not info or info.qorg_final_decision not in {"Selected","Reserve / Waitlisted"}:frappe.throw("Job Offer requires a selected or reserve candidate.")
    first=next_offer_candidate(info.job_title)
    if first and first!=applicant:frappe.throw(f"Offer sequence requires processing candidate {first} first.")
    other=frappe.db.get_value("Job Offer",{"qorg_applicant":applicant,"name":["!=",doc.name or ""],"qorg_response_status":["in",list(ACTIVE_OFFER_STATES)]},"name")
    if other:frappe.throw(f"An active Job Offer already exists: {other}")
    doc.qorg_selection_priority=info.qorg_selection_priority
    if doc.qorg_valid_until and getattr(doc,"offer_date",None) and getdate(doc.qorg_valid_until)<getdate(doc.offer_date):frappe.throw("Valid Until cannot be before Offer Date.")

def default_offer_validity(doc):
    if not doc.qorg_valid_until and getattr(doc,"offer_date",None):doc.qorg_valid_until=add_days(doc.offer_date,get_settings().offer_validity_days)

def update_applicant_offer_state(offer):
    applicant=offer.qorg_applicant or getattr(offer,"job_applicant",None)
    if not applicant:return
    mapping={"Draft":"Offer In Preparation","Issued":"Offer Issued","Accepted":"Offer Accepted","Rejected":"Offer Declined","Expired":"Offer Expired","Withdrawn":"Closed"}
    values={"qorg_selection_status":mapping.get(offer.qorg_response_status,"Pending Decision"),"qorg_job_offer":offer.name}
    if offer.qorg_response_status in TERMINAL_OFFER_STATES:
        opening=frappe.db.get_value("Job Applicant",applicant,"job_title");offer.qorg_next_candidate=next_offer_candidate(opening,applicant);values["qorg_next_action"]="Proceed with next ranked candidate" if offer.qorg_next_candidate else "Review recruitment queue"
    elif offer.qorg_response_status=="Accepted":values["qorg_next_action"]="Issue appointment letter"
    frappe.db.set_value("Job Applicant",applicant,values,update_modified=False)

def sync_appointment_state(doc):
    if not doc.qorg_job_offer:return
    offer=frappe.db.get_value("Job Offer",doc.qorg_job_offer,["qorg_response_status","qorg_applicant"],as_dict=True)
    if not offer or offer.qorg_response_status!="Accepted":frappe.throw("Appointment Letter requires an Accepted Job Offer.")
    doc.qorg_job_applicant=offer.qorg_applicant;doc.qorg_external_person=frappe.db.get_value("Job Applicant",offer.qorg_applicant,"qorg_external_person")

def sync_employee_trace(doc):
    if not doc.qorg_job_applicant:return
    applicant=frappe.db.get_value("Job Applicant",doc.qorg_job_applicant,["qorg_external_person","qorg_job_offer","qorg_selection_status"],as_dict=True)
    if not applicant:return
    if applicant.qorg_selection_status not in {"Offer Accepted","Appointment Issued","Employee Created"}:frappe.throw("Employee creation requires an accepted offer and appointment process.")
    doc.qorg_external_person=applicant.qorg_external_person;doc.qorg_job_offer=applicant.qorg_job_offer

def after_employee_insert(doc):
    if doc.qorg_job_applicant:frappe.db.set_value("Job Applicant",doc.qorg_job_applicant,{"qorg_employee":doc.name,"qorg_selection_status":"Employee Created","qorg_next_action":"Start employee onboarding"},update_modified=False)
