import frappe
from frappe import _
def _base_execute(filters=None):
    filters=frappe._dict(filters or {}); conditions={}
    for key in ("company","external_opportunity","assigned_reviewer"):
        if filters.get(key): conditions[key]=filters.get(key)
    if filters.get("status"): conditions["status"]=("in",filters.status)
    if filters.get("from_date"): conditions["application_date"]=(">=",filters.from_date)
    rows=frappe.get_list("Volunteer Application",filters=conditions,fields=["name","applicant_name","external_person","external_opportunity","status","application_date","assigned_reviewer","screening_score","final_decision","modified"],order_by="modified desc")
    if filters.get("to_date"): rows=[r for r in rows if not r.application_date or str(r.application_date)<=str(filters.to_date)]
    columns=[{"label":_("Application"),"fieldname":"name","fieldtype":"Link","options":"Volunteer Application","width":170,"sticky":True,"show_title":True},{"label":_("Applicant"),"fieldname":"applicant_name","fieldtype":"Data","width":210,"sticky":True},{"label":_("External Person"),"fieldname":"external_person","fieldtype":"Link","options":"External Person","width":170,"show_title":True},{"label":_("Opportunity"),"fieldname":"external_opportunity","fieldtype":"Link","options":"External Opportunity","width":180,"show_title":True},{"label":_("Status"),"fieldname":"status","fieldtype":"Data","width":125},{"label":_("Application Date"),"fieldname":"application_date","fieldtype":"Date","width":110},{"label":_("Reviewer"),"fieldname":"assigned_reviewer","fieldtype":"Link","options":"User","width":160,"show_title":True},{"label":_("Score"),"fieldname":"screening_score","fieldtype":"Float","width":85},{"label":_("Decision"),"fieldname":"final_decision","fieldtype":"Data","width":110}]
    counts={}
    for row in rows: counts[row.status]=counts.get(row.status,0)+1
    chart={"data":{"labels":list(counts),"datasets":[{"name":_("Applications"),"values":list(counts.values())}]},"type":"bar","height":260,"colors":["#449CF0"]}
    summary=[{"label":_("Applications"),"value":len(rows),"indicator":"blue"},{"label":_("Approved"),"value":counts.get("Approved",0),"indicator":"green"},{"label":_("In Review"),"value":counts.get("Under Review",0)+counts.get("Under Screening",0),"indicator":"orange"},{"label":_("Rejected"),"value":counts.get("Rejected",0),"indicator":"red"}]
    return columns,rows,None,chart,summary


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
