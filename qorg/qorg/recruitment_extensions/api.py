from __future__ import annotations
import frappe
from frappe.utils import now,today
from qorg.qorg.recruitment_extensions.services import FINAL_DECISIONS,interview_scores,overall_score,next_offer_candidate

def _manager():
    if frappe.session.user!="Administrator" and not ({"HR Manager","Recruitment Manager"}&set(frappe.get_roles())):frappe.throw("Recruitment management role is required.",frappe.PermissionError)
@frappe.whitelist(methods=["POST"])
def complete_screening(name,status,remarks=None):
    doc=frappe.get_doc("Job Applicant",name);doc.check_permission("write")
    if status not in {"Eligible","Shortlisted","Not Eligible"}:frappe.throw("Invalid screening status.")
    doc.qorg_screening_status=status;doc.qorg_screening_reviewer=frappe.session.user;doc.qorg_screening_remarks=remarks;doc.save();return doc.name
@frappe.whitelist(methods=["POST"])
def record_final_decision(name,decision,remarks=None,priority=None):
    _manager()
    if decision not in FINAL_DECISIONS:frappe.throw("Invalid decision.")
    if decision in {"Selected","Reserve / Waitlisted"} and (not priority or int(priority)<1):frappe.throw("Selection Priority is required for selected and reserve candidates.")
    doc=frappe.get_doc("Job Applicant",name);doc.check_permission("write")
    score,missing,failed=interview_scores(name)
    if decision in {"Selected","Reserve / Waitlisted"} and (missing or failed):frappe.throw("Mandatory assessments incomplete or failed: "+", ".join(missing+failed))
    if priority:
        duplicate=frappe.db.get_value("Job Applicant",{"job_title":doc.job_title,"qorg_selection_priority":int(priority),"qorg_final_decision":["in",["Selected","Reserve / Waitlisted"]],"name":["!=",doc.name]},"name")
        if duplicate:frappe.throw(f"Selection Priority {priority} is already assigned to {duplicate}.")
    if not remarks:frappe.throw("Evidence-based rationale is required.")
    final_score=overall_score(name,score);status="Primary Candidate" if int(priority or 0)==1 and decision=="Selected" else "Reserve Candidate" if decision in {"Selected","Reserve / Waitlisted"} else "Closed"
    doc.qorg_final_decision=decision;doc.qorg_interview_score=score;doc.qorg_overall_score=final_score;doc.qorg_rank=priority;doc.qorg_selection_priority=priority;doc.qorg_selection_status=status;doc.qorg_selected_on=now();doc.qorg_next_action="Prepare offer" if status=="Primary Candidate" else "Await primary candidate outcome" if status=="Reserve Candidate" else "None"
    doc.append("qorg_decision_log",{"decision":decision,"decision_date":today(),"decision_by":frappe.session.user,"screening_score":doc.qorg_screening_score,"interview_score":score,"overall_score":final_score,"rank":priority,"remarks":remarks})
    doc.save();return doc.name
@frappe.whitelist()
def get_next_offer_candidate(job_opening):
    _manager();return {"job_applicant":next_offer_candidate(job_opening)}
@frappe.whitelist(methods=["POST"])
def respond_to_offer(name,response,remarks=None):
    if response not in {"Accepted","Rejected"}:frappe.throw("Invalid response.")
    doc=frappe.get_doc("Job Offer",name);doc.check_permission("write");doc.qorg_response_status=response;doc.qorg_response_date=today();doc.qorg_response_remarks=remarks;doc.save();return {"job_offer":doc.name,"next_candidate":doc.qorg_next_candidate}
