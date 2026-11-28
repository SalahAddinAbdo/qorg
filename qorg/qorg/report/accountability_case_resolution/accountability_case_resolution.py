import frappe
from qorg.qorg.governance_accountability.reporting import chart, date_range, overdue, summary, view_columns

def execute(filters=None):
    filters=frappe._dict(filters or {})
    columns=[
        {"label":"Case","fieldname":"name","fieldtype":"Link","options":'Accountability Case',"width":150},
        {"label":"Subject","fieldname":"subject","fieldtype":"Data","options":None,"width":220},
        {"label":"Type","fieldname":"case_type","fieldtype":"Link","options":'Accountability Case Type',"width":130},
        {"label":"Category","fieldname":"category","fieldtype":"Link","options":'Accountability Category',"width":140},
        {"label":"Company","fieldname":"company","fieldtype":"Link","options":'Company',"width":130},
        {"label":"Project","fieldname":"project","fieldtype":"Link","options":'Project',"width":130},
        {"label":"Status","fieldname":"status","fieldtype":"Data","options":None,"width":120},
        {"label":"Priority","fieldname":"priority","fieldtype":"Data","options":None,"width":85},
        {"label":"Received","fieldname":"received_on","fieldtype":"Datetime","options":None,"width":140},
        {"label":"Due","fieldname":"response_due_on","fieldtype":"Datetime","options":None,"width":140},
        {"label":"Overdue","fieldname":"overdue","fieldtype":"Check","options":None,"width":75},
    ]
    allowed=set(['case_type', 'category', 'company', 'project', 'status', 'priority', 'received_on', 'response_due_on'])
    allowed.update({'channel','procurement_process'})
    db={k:v for k,v in filters.items() if k in allowed and v not in (None,"")}
    db.update(date_range(filters,"received_on"))
    fields=[c["fieldname"] for c in columns if c["fieldname"]!="overdue"]
    rows=frappe.get_list("Accountability Case",fields=fields,filters=db,order_by="modified desc",limit_page_length=2000)
    for row in rows: row.overdue=overdue(row.get("due_date") or row.get("response_due_on") or row.get("next_review_date"),row.get("status"))
    return view_columns(columns,filters.get("view") or "Full"),rows,None,chart(rows,"status","Accountability Case Resolution"),summary(rows, "current_compliance_status" if "current_compliance_status" in fields else "status")
