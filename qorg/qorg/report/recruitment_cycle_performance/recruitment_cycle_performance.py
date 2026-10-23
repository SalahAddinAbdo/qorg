import frappe
from frappe import _
from frappe.utils import date_diff,today
def execute(filters=None):
 f=frappe._dict(filters or {});conditions={}
 if f.get("job_title"):conditions["job_title"]=f.job_title
 rows=frappe.get_list("Job Applicant",filters=conditions,fields=["name","applicant_name","job_title","creation","qorg_screening_status","qorg_selected_on","qorg_selection_status","modified"],order_by="creation desc")
 for r in rows:r.age_days=date_diff(today(),r.creation);r.days_to_selection=date_diff(r.qorg_selected_on,r.creation) if r.qorg_selected_on else None
 cols=[{"label":_("Applicant"),"fieldname":"name","fieldtype":"Link","options":"Job Applicant","width":170,"sticky":True,"show_title":True},{"label":_("Applicant Name"),"fieldname":"applicant_name","width":210,"sticky":True},{"label":_("Job Opening"),"fieldname":"job_title","fieldtype":"Link","options":"Job Opening","width":180,"show_title":True},{"label":_("Screening"),"fieldname":"qorg_screening_status","width":120},{"label":_("Selection Status"),"fieldname":"qorg_selection_status","width":145},{"label":_("Age Days"),"fieldname":"age_days","fieldtype":"Int","width":85},{"label":_("Days to Selection"),"fieldname":"days_to_selection","fieldtype":"Int","width":115}]
 selected=[r.days_to_selection for r in rows if r.days_to_selection is not None];avg=round(sum(selected)/len(selected),1) if selected else 0
 summary=[{"label":_("Applications"),"value":len(rows),"indicator":"blue"},{"label":_("Average Days to Selection"),"value":avg,"indicator":"orange"}]
 return cols,rows,None,None,summary
