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
