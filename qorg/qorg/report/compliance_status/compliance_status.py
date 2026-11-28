import frappe
from qorg.qorg.governance_accountability.reporting import chart, date_range, overdue, summary, view_columns

def execute(filters=None):
    filters=frappe._dict(filters or {})
    columns=[
        {"label":"Obligation","fieldname":"name","fieldtype":"Link","options":'Compliance Obligation',"width":150},
        {"label":"Title","fieldname":"obligation_title","fieldtype":"Data","options":None,"width":220},
        {"label":"Company","fieldname":"company","fieldtype":"Link","options":'Company',"width":130},
        {"label":"Project","fieldname":"project","fieldtype":"Link","options":'Project',"width":120},
        {"label":"Source","fieldname":"source_type","fieldtype":"Data","options":None,"width":120},
        {"label":"Status","fieldname":"status","fieldtype":"Data","options":None,"width":110},
        {"label":"Compliance","fieldname":"current_compliance_status","fieldtype":"Data","options":None,"width":130},
        {"label":"Responsible User","fieldname":"responsible_user","fieldtype":"Link","options":'User',"width":140},
        {"label":"Next Review","fieldname":"next_review_date","fieldtype":"Date","options":None,"width":110},
        {"label":"Overdue Review","fieldname":"overdue","fieldtype":"Check","options":None,"width":100},
    ]
    allowed=set(['company', 'project', 'source_type', 'status', 'current_compliance_status', 'responsible_user', 'next_review_date'])
    db={k:v for k,v in filters.items() if k in allowed and v not in (None,"")}
    db.update(date_range(filters,"modified"))
    fields=[c["fieldname"] for c in columns if c["fieldname"]!="overdue"]
    rows=frappe.get_list("Compliance Obligation",fields=fields,filters=db,order_by="modified desc",limit_page_length=2000)
    for row in rows: row.overdue=overdue(row.get("due_date") or row.get("response_due_on") or row.get("next_review_date"),row.get("status"))
    return view_columns(columns,filters.get("view") or "Full"),rows,None,chart(rows,"current_compliance_status","Compliance Status"),summary(rows, "current_compliance_status" if "current_compliance_status" in fields else "status")
