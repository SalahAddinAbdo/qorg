import frappe
from qorg.qorg.governance_accountability.reporting import chart, date_range, overdue, summary, view_columns

def execute(filters=None):
    filters=frappe._dict(filters or {})
    columns=[
        {"label":"Risk","fieldname":"name","fieldtype":"Link","options":'Enterprise Risk',"width":150},
        {"label":"Title","fieldname":"risk_title","fieldtype":"Data","options":None,"width":220},
        {"label":"Company","fieldname":"company","fieldtype":"Link","options":'Company',"width":130},
        {"label":"Category","fieldname":"risk_category","fieldtype":"Data","options":None,"width":120},
        {"label":"Owner","fieldname":"risk_owner","fieldtype":"Link","options":'User',"width":140},
        {"label":"Status","fieldname":"status","fieldtype":"Data","options":None,"width":110},
        {"label":"Priority","fieldname":"priority","fieldtype":"Data","options":None,"width":85},
        {"label":"Next Review","fieldname":"next_review_date","fieldtype":"Date","options":None,"width":110},
        {"label":"Overdue Review","fieldname":"overdue","fieldtype":"Check","options":None,"width":100},
    ]
    allowed=set(['company', 'risk_category', 'risk_owner', 'status', 'priority', 'next_review_date'])
    db={k:v for k,v in filters.items() if k in allowed and v not in (None,"")}
    db.update(date_range(filters,"modified"))
    fields=[c["fieldname"] for c in columns if c["fieldname"]!="overdue"]
    rows=frappe.get_list("Enterprise Risk",fields=fields,filters=db,order_by="modified desc",limit_page_length=2000)
    for row in rows: row.overdue=overdue(row.get("due_date") or row.get("response_due_on") or row.get("next_review_date"),row.get("status"))
    return view_columns(columns,filters.get("view") or "Full"),rows,None,chart(rows,"priority","Enterprise Risk Register"),summary(rows, "current_compliance_status" if "current_compliance_status" in fields else "status")
