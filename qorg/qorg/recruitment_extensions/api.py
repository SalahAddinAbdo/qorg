from __future__ import annotations
import frappe
from frappe import _
from frappe.utils import now, today
from . import services

def _manager():
    if frappe.session.user!="Administrator" and not ({"HR Manager","Recruitment Manager"}&set(frappe.get_roles())): frappe.throw(_("Recruitment management role is required."),frappe.PermissionError)

def _doc(dt,name,perm="read"):
    d=frappe.get_doc(dt,name); d.check_permission(perm); return d

@frappe.whitelist(methods=["POST"])
def complete_screening(name,status,remarks=None):
    d=_doc("Job Applicant",name,"write"); services.sync_screening_criteria(d)
    if status not in {"Eligible","Shortlisted","Not Eligible"}: frappe.throw(_("Invalid screening status."))
    d.qorg_screening_status=status; d.qorg_screening_reviewer=frappe.session.user; d.qorg_screening_remarks=remarks; d.save(); services.recalculate_applicant(d.name); return d.name

@frappe.whitelist(methods=["POST"])
def record_final_decision(name,decision,remarks,priority=None):
    _manager(); d=_doc("Job Applicant",name,"write")
    d.qorg_final_decision=decision; d.qorg_selection_priority=priority; d.qorg_decision_rationale=remarks; d.qorg_decision_by=frappe.session.user; d.qorg_decision_date=today(); services.validate_final_decision(d); d.save(); return d.name

@frappe.whitelist()
def recalculate_recruitment_scores(name):
    _doc("Job Applicant",name,"read"); return services.recalculate_applicant(name)

@frappe.whitelist(methods=["POST"])
def create_job_offer(applicant):
    _manager(); a=_doc("Job Applicant",applicant,"read"); services.validate_final_decision(a)
    existing=frappe.db.get_value("Job Offer",{"qorg_job_applicant":a.name,"qorg_response_status":["not in",["Rejected","Expired","Withdrawn"]]},"name")
    if existing:return existing
    nxt=services.next_offer_candidate(services.linked_job_opening(a))
    if nxt and nxt!=a.name: frappe.throw(_("A higher-priority candidate must be processed first: {0}").format(nxt))
    offer=frappe.new_doc("Job Offer"); offer.applicant=a.name if hasattr(offer,"applicant") else None; offer.qorg_job_applicant=a.name; services.copy_context(a,offer); offer.insert(); return offer.name

@frappe.whitelist(methods=["POST"])
def record_offer_response(offer,response,remarks=None):
    _manager(); d=_doc("Job Offer",offer,"write")
    if response not in {"Accepted","Rejected","Expired","Withdrawn"}: frappe.throw(_("Invalid offer response."))
    d.qorg_response_status=response; d.qorg_response_date=today(); d.qorg_response_remarks=remarks; d.save()
    if d.qorg_job_applicant:
        status="Offer Accepted" if response=="Accepted" else response
        frappe.db.set_value("Job Applicant",d.qorg_job_applicant,{"qorg_selection_status":status,"qorg_next_action":"Create Appointment Letter" if response=="Accepted" else "Proceed with next ranked candidate"},update_modified=False)
    return {"offer":d.name,"next_candidate":services.next_offer_candidate(frappe.db.get_value("Job Applicant",d.qorg_job_applicant,"job_title")) if response!="Accepted" and d.qorg_job_applicant else None}

@frappe.whitelist(methods=["POST"])
def create_appointment_letter(offer):
    _manager(); o=_doc("Job Offer",offer,"read")
    if o.qorg_response_status!="Accepted": frappe.throw(_("Only an accepted offer can create an appointment letter."))
    existing=frappe.db.get_value("Appointment Letter",{"qorg_job_offer":o.name},"name")
    if existing:return existing
    d=frappe.new_doc("Appointment Letter"); d.qorg_job_offer=o.name; d.qorg_external_person=o.get("qorg_external_person"); services.copy_context(o,d); d.insert(); return d.name

@frappe.whitelist(methods=["POST"])
def create_employee_from_appointment(appointment_letter):
    _manager(); al=_doc("Appointment Letter",appointment_letter,"read")
    applicant=frappe.db.get_value("Job Offer",al.qorg_job_offer,"qorg_job_applicant") if al.qorg_job_offer else None
    if not applicant: frappe.throw(_("Job Applicant link is required."))
    existing=frappe.db.get_value("Employee",{"qorg_job_applicant":applicant},"name")
    if existing:return existing
    a=frappe.get_doc("Job Applicant",applicant); e=frappe.new_doc("Employee")
    for target,source in (("first_name","applicant_name"),("personal_email","email_id"),("cell_number","phone_number")): 
        if hasattr(e,target) and a.get(source): e.set(target,a.get(source))
    e.qorg_job_applicant=a.name; e.qorg_external_person=a.get("qorg_external_person"); services.copy_context(a,e); e.insert(); frappe.db.set_value("Job Applicant",a.name,{"qorg_selection_status":"Employee Created","qorg_next_action":"Start Employee Onboarding"},update_modified=False); return e.name
