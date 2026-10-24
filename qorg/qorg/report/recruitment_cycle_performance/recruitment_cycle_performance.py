import frappe
from frappe import _
from frappe.utils import date_diff,today
def _base_execute(filters=None):
 f=frappe._dict(filters or {});conditions={}
 if f.get("job_title"):conditions["job_title"]=f.job_title
 rows=frappe.get_list("Job Applicant",filters=conditions,fields=["name","applicant_name","job_title","creation","qorg_screening_status","qorg_selected_on","qorg_selection_status","modified"],order_by="creation desc")
 for r in rows:r.age_days=date_diff(today(),r.creation);r.days_to_selection=date_diff(r.qorg_selected_on,r.creation) if r.qorg_selected_on else None
 cols=[{"label":_("Applicant"),"fieldname":"name","fieldtype":"Link","options":"Job Applicant","width":170,"sticky":True,"show_title":True},{"label":_("Applicant Name"),"fieldname":"applicant_name","width":210,"sticky":True},{"label":_("Job Opening"),"fieldname":"job_title","fieldtype":"Link","options":"Job Opening","width":180,"show_title":True},{"label":_("Screening"),"fieldname":"qorg_screening_status","width":120},{"label":_("Selection Status"),"fieldname":"qorg_selection_status","width":145},{"label":_("Age Days"),"fieldname":"age_days","fieldtype":"Int","width":85},{"label":_("Days to Selection"),"fieldname":"days_to_selection","fieldtype":"Int","width":115}]
 selected=[r.days_to_selection for r in rows if r.days_to_selection is not None];avg=round(sum(selected)/len(selected),1) if selected else 0
 summary=[{"label":_("Applications"),"value":len(rows),"indicator":"blue"},{"label":_("Average Days to Selection"),"value":avg,"indicator":"orange"}]
 return cols,rows,None,None,summary


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
