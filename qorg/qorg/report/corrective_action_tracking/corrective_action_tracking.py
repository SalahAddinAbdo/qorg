import frappe
from qorg.qorg.governance_accountability.reporting import chart, date_range, overdue, summary, view_columns

def execute(filters=None):
    filters=frappe._dict(filters or {})
    columns=[
        {"label":"Action","fieldname":"name","fieldtype":"Link","options":'Corrective Action',"width":150},
        {"label":"Subject","fieldname":"subject","fieldtype":"Data","options":None,"width":220},
        {"label":"Company","fieldname":"company","fieldtype":"Link","options":'Company',"width":130},
        {"label":"Project","fieldname":"project","fieldtype":"Link","options":'Project',"width":120},
        {"label":"Status","fieldname":"status","fieldtype":"Data","options":None,"width":120},
        {"label":"Priority","fieldname":"priority","fieldtype":"Data","options":None,"width":85},
        {"label":"Responsible","fieldname":"responsible_user","fieldtype":"Link","options":'User',"width":140},
        {"label":"Department","fieldname":"responsible_department","fieldtype":"Link","options":'Department',"width":130},
        {"label":"Due","fieldname":"due_date","fieldtype":"Date","options":None,"width":105},
        {"label":"Effectiveness","fieldname":"effectiveness_result","fieldtype":"Data","options":None,"width":120},
        {"label":"Overdue","fieldname":"overdue","fieldtype":"Check","options":None,"width":75},
    ]
    allowed=set(['company', 'project', 'status', 'priority', 'responsible_user', 'responsible_department', 'due_date', 'effectiveness_result'])
    db={k:v for k,v in filters.items() if k in allowed and v not in (None,"")}
    db.update(date_range(filters,"modified"))
    fields=[c["fieldname"] for c in columns if c["fieldname"]!="overdue"]
    rows=frappe.get_list("Corrective Action",fields=fields,filters=db,order_by="modified desc",limit_page_length=2000)
    for row in rows: row.overdue=overdue(row.get("due_date") or row.get("response_due_on") or row.get("next_review_date"),row.get("status"))
    return view_columns(columns,filters.get("view") or "Full"),rows,None,chart(rows,"status","Corrective Action Tracking"),summary(rows, "current_compliance_status" if "current_compliance_status" in fields else "status")
