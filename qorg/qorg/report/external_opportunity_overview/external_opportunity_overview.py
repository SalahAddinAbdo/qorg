import frappe
from frappe import _
def _base_execute(filters=None):
    filters=frappe._dict(filters or {}); conditions={}
    for key in ("company","opportunity_type"): 
        if filters.get(key): conditions[key]=filters.get(key)
    if filters.get("status"): conditions["status"]=("in",filters.get("status"))
    if filters.get("closing_from"): conditions["closing_date"]=(">=",filters.closing_from)
    rows=frappe.get_list("External Opportunity",filters=conditions,fields=["name","opportunity_title","opportunity_type","status","company","closing_date","application_count","responsible_employee","modified"],order_by="closing_date asc, modified desc")
    if filters.get("closing_to"): rows=[r for r in rows if not r.closing_date or str(r.closing_date)<=str(filters.closing_to)]
    columns=[{"label":_("Opportunity"),"fieldname":"name","fieldtype":"Link","options":"External Opportunity","width":170,"sticky":True,"show_title":True},{"label":_("Title"),"fieldname":"opportunity_title","fieldtype":"Data","width":230,"sticky":True},{"label":_("Type"),"fieldname":"opportunity_type","fieldtype":"Data","width":115},{"label":_("Status"),"fieldname":"status","fieldtype":"Data","width":110},{"label":_("Company"),"fieldname":"company","fieldtype":"Link","options":"Company","width":170,"show_title":True},{"label":_("Closing Date"),"fieldname":"closing_date","fieldtype":"Date","width":110},{"label":_("Applications"),"fieldname":"application_count","fieldtype":"Int","width":100},{"label":_("Responsible Employee"),"fieldname":"responsible_employee","fieldtype":"Link","options":"Employee","width":170,"show_title":True}]
    counts={}
    for row in rows: counts[row.status]=counts.get(row.status,0)+1
    chart={"data":{"labels":list(counts),"datasets":[{"name":_("Opportunities"),"values":list(counts.values())}]},"type":"donut","height":260}
    total=sum((r.application_count or 0) for r in rows); published=counts.get("Published",0)
    summary=[{"label":_("Opportunities"),"value":len(rows),"indicator":"blue"},{"label":_("Published"),"value":published,"indicator":"green"},{"label":_("Applications"),"value":total,"indicator":"orange"}]
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
