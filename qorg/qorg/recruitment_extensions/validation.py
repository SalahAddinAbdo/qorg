from . import services

def validate_designation(doc, method=None):
    if hasattr(services, "validate_designation"): services.validate_designation(doc)

def validate_job_opening(doc, method=None): services.validate_weights(doc)
def validate_interview_type(doc, method=None): services.validate_interview_type(doc)
def validate_feedback(doc, method=None): services.calculate_feedback(doc, require_evidence=bool(doc.docstatus))
