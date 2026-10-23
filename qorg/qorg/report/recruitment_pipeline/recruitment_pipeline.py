import frappe
from frappe import _
def execute(filters=None):
 f=frappe._dict(filters or {});conditions={k:f.get(k) for k in ("status","qorg_screening_status","qorg_final_decision") if f.get(k)}
 rows=frappe.get_list("Job Applicant",filters=conditions,fields=["name","applicant_name","job_title","status","qorg_screening_status","qorg_final_decision","qorg_overall_score","qorg_external_person"],order_by="modified desc")
 cols=[{"label":_("Applicant"),"fieldname":"name","fieldtype":"Link","options":"Job Applicant","width":170,"sticky":True,"show_title":True},{"label":_("Applicant Name"),"fieldname":"applicant_name","width":210,"sticky":True},{"label":_("Job Opening"),"fieldname":"job_title","fieldtype":"Link","options":"Job Opening","width":180,"show_title":True},{"label":_("Status"),"fieldname":"status","width":120},{"label":_("Screening"),"fieldname":"qorg_screening_status","width":120},{"label":_("Decision"),"fieldname":"qorg_final_decision","width":140},{"label":_("Score"),"fieldname":"qorg_overall_score","fieldtype":"Float","width":90}]
 counts={}
 for r in rows:counts[r.qorg_final_decision or r.qorg_screening_status or r.status]=counts.get(r.qorg_final_decision or r.qorg_screening_status or r.status,0)+1
 chart={"data":{"labels":list(counts),"datasets":[{"name":_("Applicants"),"values":list(counts.values())}]},"type":"donut","height":260}
 summary=[{"label":_("Applicants"),"value":len(rows),"indicator":"blue"},{"label":_("Selected"),"value":counts.get("Selected",0),"indicator":"green"},{"label":_("Shortlisted"),"value":counts.get("Shortlisted",0),"indicator":"orange"}]
 return cols,rows,None,chart,summary
