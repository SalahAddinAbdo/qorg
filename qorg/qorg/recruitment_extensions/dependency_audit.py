import frappe
OWNED=["Designation Interview Criterion","Recruitment Screening Template Criterion","Applicant Screening Criterion","Recruitment Decision Log","Recruitment Assessment Stage","Interview Evaluation Criterion","Interview Criterion Score"]
REQUIRED=["Designation","Interview Type","Interview","Interview Feedback","Job Opening","Job Applicant","Job Offer","Appointment Letter","Employee","Employee Onboarding","Employee Boarding Activity","Project","Branch"]
def audit():
 if frappe.session.user!="Administrator": frappe.throw("Administrator only",frappe.PermissionError)
 missing=[x for x in REQUIRED+OWNED if not frappe.db.exists("DocType",x)]
 return {"ok":not missing,"missing":missing,"incompatible":[]}
