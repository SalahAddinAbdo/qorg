import frappe
from frappe import _
def _base_execute(filters=None):
 rows=frappe.get_list("Job Applicant",fields=["name","applicant_name","job_title","qorg_screening_status","qorg_screening_reviewer","qorg_screening_score","creation"],order_by="creation asc")
 cols=[{"label":_("Applicant"),"fieldname":"name","fieldtype":"Link","options":"Job Applicant","width":170,"sticky":True,"show_title":True},{"label":_("Applicant Name"),"fieldname":"applicant_name","width":210,"sticky":True},{"label":_("Job Opening"),"fieldname":"job_title","fieldtype":"Link","options":"Job Opening","width":180,"show_title":True},{"label":_("Screening"),"fieldname":"qorg_screening_status","width":120},{"label":_("Reviewer"),"fieldname":"qorg_screening_reviewer","fieldtype":"Link","options":"User","width":170},{"label":_("Score"),"fieldname":"qorg_screening_score","fieldtype":"Float","width":90},{"label":_("Received"),"fieldname":"creation","fieldtype":"Datetime","width":140}]
 return cols,rows


def _normalize_result(result):
    values=list(result) if isinstance(result,(tuple,list)) else [[],[]]
    while len(values)<6: values.append(None)
    columns,rows,message,chart,summary,skip_total=values[:6]
    columns=columns or [];rows=rows or []
    for index,column in enumerate(columns):
        if isinstance(column,dict): column["sticky"]=bool(index<2)
    if not summary:
        summary=[{"label":_("Total Records"),"value":len(rows),"indicator":"blue","datatype":"Int"}]
        status_field=next((c.get("fieldname") for c in columns if isinstance(c,dict) and c.get("fieldname") in ("status","qorg_selection_status","qorg_screening_status","result")),None)
        if status_field:
            counts={}
            for row in rows:
                label=(row.get(status_field) if hasattr(row,"get") else None) or _("Not Set");counts[label]=counts.get(label,0)+1
            summary.extend({"label":label,"value":value,"indicator":"blue","datatype":"Int"} for label,value in counts.items() if value)
            if not chart and counts: chart={"data":{"labels":list(counts),"datasets":[{"name":_("Records"),"values":list(counts.values())}]},"type":"donut","height":260}
    try:
        from qorg.qorg.project_management.report_link_titles import finalize_report_result
        result=finalize_report_result(columns,rows,message,chart,summary,1)
        return result if result else (columns,rows,message,chart,summary,1)
    except Exception:
        return columns,rows,message,chart,summary,1

def execute(filters=None):
    return _normalize_result(_base_execute(filters or {}))
