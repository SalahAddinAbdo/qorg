import frappe
from frappe import _
def execute(filters=None):
    meta=frappe.get_meta("Interview")
    type_field="interview_type" if meta.has_field("interview_type") else "interview_round"
    rows=frappe.get_list("Interview",fields=["name","job_applicant",type_field,"status","qorg_attendance_status","qorg_final_score","scheduled_on"],order_by="scheduled_on asc")
    for row in rows:
        row.interview_type=row.get(type_field)
    cols=[{"label":_("Interview"),"fieldname":"name","fieldtype":"Link","options":"Interview","width":170,"sticky":True},{"label":_("Applicant"),"fieldname":"job_applicant","fieldtype":"Link","options":"Job Applicant","width":190,"sticky":True,"show_title":True},{"label":_("Interview Type"),"fieldname":"interview_type","fieldtype":"Link","options":"Interview Type","width":170,"show_title":True},{"label":_("Status"),"fieldname":"status","width":110},{"label":_("Attendance"),"fieldname":"qorg_attendance_status","width":110},{"label":_("Score"),"fieldname":"qorg_final_score","fieldtype":"Float","width":90},{"label":_("Scheduled"),"fieldname":"scheduled_on","fieldtype":"Datetime","width":150}]
    return cols,rows
