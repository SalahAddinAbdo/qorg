import frappe
from qorg.qorg.governance_accountability.reporting import chart, date_range, overdue, summary, view_columns

def execute(filters=None):
    filters=frappe._dict(filters or {})
    columns=[
        {"label":"Finding","fieldname":"name","fieldtype":"Link","options":'Assurance Finding',"width":150},
        {"label":"Title","fieldname":"finding_title","fieldtype":"Data","options":None,"width":220},
        {"label":"Company","fieldname":"company","fieldtype":"Link","options":'Company',"width":130},
        {"label":"Project","fieldname":"project","fieldtype":"Link","options":'Project',"width":120},
        {"label":"Source","fieldname":"source_type","fieldtype":"Data","options":None,"width":120},
        {"label":"Classification","fieldname":"classification","fieldtype":"Data","options":None,"width":150},
        {"label":"Status","fieldname":"status","fieldtype":"Data","options":None,"width":110},
        {"label":"Responsible","fieldname":"responsible_user","fieldtype":"Link","options":'User',"width":140},
        {"label":"Due","fieldname":"due_date","fieldtype":"Date","options":None,"width":105},
        {"label":"CAPA","fieldname":"corrective_action","fieldtype":"Link","options":'Corrective Action',"width":130},
        {"label":"Overdue","fieldname":"overdue","fieldtype":"Check","options":None,"width":75},
    ]
    allowed=set(['company', 'project', 'source_type', 'classification', 'status', 'responsible_user', 'due_date', 'corrective_action'])
    db={k:v for k,v in filters.items() if k in allowed and v not in (None,"")}
    db.update(date_range(filters,"modified"))
    fields=[c["fieldname"] for c in columns if c["fieldname"]!="overdue"]
    rows=frappe.get_list("Assurance Finding",fields=fields,filters=db,order_by="modified desc",limit_page_length=2000)
    for row in rows: row.overdue=overdue(row.get("due_date") or row.get("response_due_on") or row.get("next_review_date"),row.get("status"))
    return view_columns(columns,filters.get("view") or "Full"),rows,None,chart(rows,"classification","Assurance Findings"),summary(rows, "current_compliance_status" if "current_compliance_status" in fields else "status")
