from __future__ import annotations
from datetime import date
import frappe

def date_range(filters,field):
    out={}
    if filters.get('from_date'):out[field]=['>=',filters.from_date]
    if filters.get('to_date'):
        out[field]=['between',[filters.get('from_date') or '1900-01-01',filters.to_date]]
    return out

def view_columns(all_columns,view):
    if view=='Executive':return [x for x in all_columns if x['fieldname'] in {'name','title','subject','risk_title','obligation_title','finding_title','status','priority','classification','current_compliance_status','due_date','next_review_date','overdue'}]
    if view=='Operations':return [x for x in all_columns if x['fieldname'] not in {'company','project'}]
    return all_columns

def overdue(due,status):return int(bool(due and str(status) not in ('Closed','Cancelled','Verified Effective') and frappe.utils.getdate(due)<date.today()))
def summary(rows,field='status'):
    return [{'value':len(rows),'label':'Total','datatype':'Int'},{'value':sum(1 for r in rows if getattr(r,'overdue',0)),'label':'Overdue','datatype':'Int'},{'value':sum(1 for r in rows if getattr(r,field,None) in ('Closed','Verified Effective','Compliant')),'label':'Completed / Compliant','datatype':'Int'}]
def chart(rows,field,label):
    values={}
    for r in rows:values[str(getattr(r,field,None) or 'Not Set')]=values.get(str(getattr(r,field,None) or 'Not Set'),0)+1
    return {'data':{'labels':list(values),'datasets':[{'name':label,'values':list(values.values())}]},'type':'bar','height':260}
