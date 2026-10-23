import frappe
OWNED=("Applicant Screening Criterion","Recruitment Decision Log","Recruitment Assessment Stage","Interview Evaluation Criterion","Interview Criterion Score")
STANDARD=("Job Requisition","Job Opening","Job Applicant","Interview Type","Interview","Interview Feedback","Job Offer","Appointment Letter","Employee","Employee Onboarding","External Person","External Opportunity")
@frappe.whitelist()
def audit():
    if frappe.session.user!="Administrator":frappe.throw("Administrator is required.",frappe.PermissionError)
    missing=[x for x in OWNED+STANDARD if not frappe.db.exists("DocType",x)]
    incompatible=[]
    for spec in __import__('json').loads(open(frappe.get_app_path("qorg","qorg","recruitment_extensions","data","custom_fields.json")).read()):
        name=f"{spec['dt']}-{spec['fieldname']}"
        if not frappe.db.exists("Custom Field",name):missing.append(name);continue
        row=frappe.db.get_value("Custom Field",name,["fieldtype","options","module"],as_dict=True)
        if row.fieldtype!=spec['fieldtype'] or (spec.get('options') and row.options!=spec.get('options')):incompatible.append(name)
    reports=("Recruitment Pipeline","Applicant Screening and Aging","Interview Progress","Offer and Appointment Tracking","Candidate Selection Queue","Recruitment Cycle Performance")
    missing_reports=[x for x in reports if not frappe.db.exists("Report",x)]
    return {"ok":not missing and not incompatible and not missing_reports,"missing":missing,"incompatible":incompatible,"missing_reports":missing_reports}
