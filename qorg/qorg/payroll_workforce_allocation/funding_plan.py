import frappe
from frappe import _
from frappe.utils import flt,getdate
from .utils import stable_hash

def _end(value): return getdate(value) if value else getdate("9999-12-31")
def validate_plan(doc):
    start,end=getdate(doc.effective_from),_end(doc.effective_to)
    if end<start: frappe.throw(_("Effective To cannot precede Effective From."))
    rows=list(doc.destinations or [])
    if not rows: frappe.throw(_("At least one funding destination is required."))
    if doc.allocation_method in ("Single Destination","Fixed Percentage"):
        total=sum(flt(x.allocation_percentage) for x in rows); diff=100-total
        if abs(diff)>0.0001: frappe.throw(_("Funding destination percentages must total 100%. Current total: {0}; required difference: {1}.").format(total,diff))
    if doc.allocation_method=="Single Destination" and len(rows)!=1: frappe.throw(_("Single Destination requires exactly one destination."))
    if sum(1 for x in rows if x.is_default)>1: frappe.throw(_("Only one destination may be default."))
    seen=set()
    for row in rows:
        key=(row.project,row.cost_center,row.funding_agreement,row.budget_line,row.effective_from,row.effective_to)
        if key in seen: frappe.throw(_("Duplicate funding destination rows are not allowed."))
        seen.add(key)
        company=frappe.db.get_value("Project",row.project,"company")
        if company and company!=doc.company: frappe.throw(_("Project {0} belongs to another company.").format(row.project))
        if row.effective_from and getdate(row.effective_from)<start: frappe.throw(_("Destination start date cannot precede the plan start date."))
        if row.effective_to and getdate(row.effective_to)>end: frappe.throw(_("Destination end date cannot exceed the plan end date."))
        if row.effective_from and row.effective_to and getdate(row.effective_to)<getdate(row.effective_from): frappe.throw(_("Destination end date cannot precede start date."))
    conflicts=frappe.db.sql("""select name from `tabWorkforce Funding Plan` where employee=%s and name!=%s and docstatus=1 and status not in ('Superseded','Expired','Cancelled') and effective_from<=%s and coalesce(effective_to,'9999-12-31')>=%s limit 2""",(doc.employee,doc.name or '',end,start),as_dict=True)
    if conflicts and doc.supersedes_plan not in {x.name for x in conflicts}: frappe.throw(_("An overlapping active funding plan exists: {0}").format(conflicts[0].name))
    doc.fingerprint=stable_hash({"employee":doc.employee,"company":doc.company,"from":doc.effective_from,"to":doc.effective_to,"method":doc.allocation_method,"rows":[x.as_dict() for x in rows]})
def activate_plan(doc):
    doc.db_set("status","Active",update_modified=False)
    if doc.supersedes_plan: frappe.db.set_value("Workforce Funding Plan",doc.supersedes_plan,"status","Superseded",update_modified=False)
def cancel_plan(doc): doc.db_set("status","Cancelled",update_modified=False)
def get_effective_plan(employee,on_date):
    rows=frappe.db.sql("""select name from `tabWorkforce Funding Plan` where employee=%s and docstatus=1 and status='Active' and effective_from<=%s and coalesce(effective_to,'9999-12-31')>=%s order by effective_from desc,modified desc limit 2""",(employee,on_date,on_date),as_dict=True)
    if len(rows)>1: frappe.throw(_("More than one active Workforce Funding Plan applies to employee {0}.").format(employee))
    return frappe.get_doc("Workforce Funding Plan",rows[0].name) if rows else None
