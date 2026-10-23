import frappe
from frappe import _
def execute(filters=None):
 rows=frappe.get_list("Job Applicant",fields=["name","applicant_name","job_title","qorg_screening_status","qorg_screening_reviewer","qorg_screening_score","creation"],order_by="creation asc")
 cols=[{"label":_("Applicant"),"fieldname":"name","fieldtype":"Link","options":"Job Applicant","width":170,"sticky":True,"show_title":True},{"label":_("Applicant Name"),"fieldname":"applicant_name","width":210,"sticky":True},{"label":_("Job Opening"),"fieldname":"job_title","fieldtype":"Link","options":"Job Opening","width":180,"show_title":True},{"label":_("Screening"),"fieldname":"qorg_screening_status","width":120},{"label":_("Reviewer"),"fieldname":"qorg_screening_reviewer","fieldtype":"Link","options":"User","width":170},{"label":_("Score"),"fieldname":"qorg_screening_score","fieldtype":"Float","width":90},{"label":_("Received"),"fieldname":"creation","fieldtype":"Datetime","width":140}]
 return cols,rows
