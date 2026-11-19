import frappe
from frappe import _
from frappe.utils import flt

def refresh_allocation_closeout(doc,method=None):
    if not doc.get("project") or not frappe.db.exists("DocType","Shared Cost Allocation Run"): return
    pending=frappe.db.count("Shared Cost Allocation Entry",{"project":doc.project,"parent":["in",frappe.get_all("Shared Cost Allocation Run",filters={"docstatus":0},pluck="name")]})
    unrecovered=0
    agreements=frappe.get_all("Funding Agreement",filters={"project":doc.project},fields=["name","indirect_cost_percent"])
    for ag in agreements:
        if not flt(ag.indirect_cost_percent): continue
        recovered=frappe.db.sql("select coalesce(sum(e.allocated_amount),0) from `tabShared Cost Allocation Entry` e join `tabShared Cost Allocation Run` r on r.name=e.parent where r.docstatus=1 and r.allocation_category='Indirect Cost Recovery' and e.project=%s and e.funding_agreement=%s",(doc.project,ag.name))[0][0]
        direct=frappe.db.sql("select coalesce(sum(debit-credit),0) from `tabGL Entry` where is_cancelled=0 and project=%s",doc.project)[0][0]
        unrecovered+=max(0,flt(direct)*flt(ag.indirect_cost_percent)/100-flt(recovered))
    if doc.meta.has_field("custom_pending_allocation_runs"): doc.custom_pending_allocation_runs=pending
    if doc.meta.has_field("custom_unrecovered_indirect_cost"): doc.custom_unrecovered_indirect_cost=unrecovered
    if doc.meta.has_field("custom_cost_allocation_closeout_status"): doc.custom_cost_allocation_closeout_status="Complete" if not pending and not unrecovered else "Pending"

def validate_allocation_closeout(doc,method=None):
    refresh_allocation_closeout(doc)
    company=frappe.db.get_value("Project",doc.project,"company") if doc.get("project") else None
    required=frappe.get_cached_value("Company",company,"custom_require_allocation_before_project_closeout") if company else 0
    if required and doc.get("status") in ("Ready for Closure","Approved"):
        blockers=[]
        if doc.get("custom_pending_allocation_runs"): blockers.append(_("pending allocation runs"))
        if flt(doc.get("custom_unrecovered_indirect_cost")): blockers.append(_("unrecovered indirect cost"))
        if blockers: frappe.throw(_("Project closeout is blocked by: {0}.").format(", ".join(blockers)))

def lock_rules_after_closure(doc,method=None):
    if doc.get("status")!="Approved" or not doc.get("project"): return
    close_date=doc.actual_closure_date or frappe.utils.nowdate()
    for name in frappe.get_all("Shared Cost Allocation Rule",filters={"docstatus":1,"status":"Active"},pluck="name"):
        rule=frappe.get_doc("Shared Cost Allocation Rule",name)
        matched=[r for r in rule.targets if r.project==doc.project and r.allow_allocation]
        if not matched: continue
        # A submitted rule remains historically immutable. Runtime validation blocks
        # the closed target. The rule ends only when every active target is closed.
        all_closed=True
        for target in [r for r in rule.targets if r.allow_allocation]:
            closed=frappe.db.exists("Project Closure",{"project":target.project,"status":"Approved"}) or frappe.db.get_value("Project",target.project,"status") in ("Completed","Cancelled")
            if not closed: all_closed=False;break
        if all_closed:
            rule.db_set("status","Superseded",update_modified=False)
            if not rule.effective_to or str(rule.effective_to)>str(close_date): rule.db_set("effective_to",close_date,update_modified=False)
