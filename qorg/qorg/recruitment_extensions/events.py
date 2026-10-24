import frappe
from . import services

def validate_job_opening(doc, method=None): services.validate_weights(doc)
def validate_interview_type(doc, method=None): services.validate_interview_type(doc)
def validate_job_applicant(doc, method=None): services.sync_screening_criteria(doc); services.validate_final_decision(doc)
def validate_interview(doc, method=None): services.configure_interview(doc)
def validate_feedback(doc, method=None): services.copy_feedback_criteria(doc); services.calculate_feedback(doc, require_evidence=bool(doc.docstatus))
def feedback_submitted(doc, method=None): services.recalculate_interview(doc.interview)
def feedback_cancelled(doc, method=None): services.recalculate_interview(doc.interview)
def feedback_deleted(doc, method=None):
    if doc.interview: services.recalculate_interview(doc.interview)
def interview_cancelled(doc, method=None):
    if doc.job_applicant: services.recalculate_applicant(doc.job_applicant)
def interview_deleted(doc, method=None):
    if doc.job_applicant: services.recalculate_applicant(doc.job_applicant)
def propagate_context(doc, method=None):
    for field in ("job_applicant","job_offer","appointment_letter"):
        if doc.get(field):
            dt={"job_applicant":"Job Applicant","job_offer":"Job Offer","appointment_letter":"Appointment Letter"}[field]
            if __import__('frappe').db.exists(dt,doc.get(field)): services.copy_context(__import__('frappe').get_doc(dt,doc.get(field)),doc); break


def validate_job_requisition_extension(doc, method=None): services.validate_job_requisition_extension(doc)
def validate_job_opening_extension(doc, method=None): services.validate_job_opening_extension(doc)
def propagate_recruitment_context(doc, method=None):
    for field,doctype in (("qorg_job_applicant","Job Applicant"),("job_applicant","Job Applicant"),("qorg_job_offer","Job Offer"),("qorg_appointment_letter","Appointment Letter")):
        value=doc.get(field)
        if value and frappe.db.exists(doctype,value):
            services.copy_recruitment_context(frappe.get_doc(doctype,value),doc);break


# Stable hook entrypoints used by qorg/hooks.py
def designation_validate(doc, method=None):
    if hasattr(services, "validate_designation"): services.validate_designation(doc)

def opening_validate(doc, method=None):
    validate_job_opening(doc, method); validate_job_opening_extension(doc, method)

def applicant_validate(doc, method=None): validate_job_applicant(doc, method)
def interview_type_validate(doc, method=None): validate_interview_type(doc, method)
def feedback_validate(doc, method=None): validate_feedback(doc, method)
def feedback_submit(doc, method=None): feedback_submitted(doc, method)
def feedback_cancel(doc, method=None): feedback_cancelled(doc, method)
def feedback_delete(doc, method=None): feedback_deleted(doc, method)
def interview_validate(doc, method=None): validate_interview(doc, method)
def interview_cancel(doc, method=None): interview_cancelled(doc, method)
def interview_trash(doc, method=None): interview_deleted(doc, method)

def offer_before_validate(doc, method=None):
    propagate_recruitment_context(doc, method)

def offer_on_update(doc, method=None):
    applicant=doc.get("qorg_job_applicant") or doc.get("job_applicant")
    if applicant and frappe.db.exists("Job Applicant",applicant):
        response=doc.get("qorg_response_status")
        values={}
        if response=="Accepted":values={"qorg_selection_status":"Offer Accepted","qorg_next_action":"Create Appointment Letter"}
        elif response in {"Rejected","Expired","Withdrawn"}:values={"qorg_selection_status":response,"qorg_next_action":"Proceed with next ranked candidate"}
        if values:frappe.db.set_value("Job Applicant",applicant,values,update_modified=False)

def appointment_validate(doc, method=None): propagate_recruitment_context(doc, method)
def appointment_on_update(doc, method=None):
    applicant=doc.get("job_applicant") or doc.get("qorg_job_applicant")
    if applicant and frappe.db.exists("Job Applicant",applicant):frappe.db.set_value("Job Applicant",applicant,{"qorg_selection_status":"Appointment Issued","qorg_next_action":"Create Employee"},update_modified=False)

def employee_validate(doc, method=None): propagate_recruitment_context(doc, method)
def employee_after_insert(doc, method=None):
    applicant=doc.get("qorg_job_applicant")
    if applicant and frappe.db.exists("Job Applicant",applicant):frappe.db.set_value("Job Applicant",applicant,{"qorg_selection_status":"Employee Created","qorg_next_action":"Create Work Commencement Notice"},update_modified=False)

def onboarding_validate(doc, method=None): propagate_recruitment_context(doc, method)


# Stable hook entrypoints used by qorg/hooks.py
def designation_validate(doc, method=None):
    if hasattr(services, "validate_designation"): services.validate_designation(doc)

def opening_validate(doc, method=None):
    validate_job_opening(doc, method); validate_job_opening_extension(doc, method)

def applicant_validate(doc, method=None): validate_job_applicant(doc, method)
def interview_type_validate(doc, method=None): validate_interview_type(doc, method)
def feedback_validate(doc, method=None): validate_feedback(doc, method)
def feedback_submit(doc, method=None): feedback_submitted(doc, method)
def feedback_cancel(doc, method=None): feedback_cancelled(doc, method)
def feedback_delete(doc, method=None): feedback_deleted(doc, method)
def interview_validate(doc, method=None): validate_interview(doc, method)
def interview_cancel(doc, method=None): interview_cancelled(doc, method)
def interview_trash(doc, method=None): interview_deleted(doc, method)

def offer_before_validate(doc, method=None):
    propagate_recruitment_context(doc, method)

def offer_on_update(doc, method=None):
    applicant=doc.get("qorg_job_applicant") or doc.get("job_applicant")
    if applicant and frappe.db.exists("Job Applicant",applicant):
        response=doc.get("qorg_response_status")
        values={}
        if response=="Accepted":values={"qorg_selection_status":"Offer Accepted","qorg_next_action":"Create Appointment Letter"}
        elif response in {"Rejected","Expired","Withdrawn"}:values={"qorg_selection_status":response,"qorg_next_action":"Proceed with next ranked candidate"}
        if values:frappe.db.set_value("Job Applicant",applicant,values,update_modified=False)

def appointment_validate(doc, method=None): propagate_recruitment_context(doc, method)
def appointment_on_update(doc, method=None):
    applicant=doc.get("job_applicant") or doc.get("qorg_job_applicant")
    if applicant and frappe.db.exists("Job Applicant",applicant):frappe.db.set_value("Job Applicant",applicant,{"qorg_selection_status":"Appointment Issued","qorg_next_action":"Create Employee"},update_modified=False)

def employee_validate(doc, method=None): propagate_recruitment_context(doc, method)
def employee_after_insert(doc, method=None):
    applicant=doc.get("qorg_job_applicant")
    if applicant and frappe.db.exists("Job Applicant",applicant):frappe.db.set_value("Job Applicant",applicant,{"qorg_selection_status":"Employee Created","qorg_next_action":"Create Work Commencement Notice"},update_modified=False)

def onboarding_validate(doc, method=None): propagate_recruitment_context(doc, method)
