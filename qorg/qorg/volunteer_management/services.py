import frappe
from frappe import _
from frappe.utils import cint, flt, getdate, now_datetime

def settings():
    hr=frappe.get_single("HR Settings")
    values={
        "require_decision_rationale":1,
        "maximum_hours_per_day":hr.get("qorg_participation_max_daily_hours") or 8,
        "maximum_hours_per_week":hr.get("qorg_participation_max_weekly_hours") or 40,
        "require_service_log_evidence":hr.get("qorg_participation_require_evidence") or 0,
        "require_supervisor_verification":hr.get("qorg_participation_require_supervisor_verification") if hr.get("qorg_participation_require_supervisor_verification") is not None else 1,
        "allow_overachievement":hr.get("qorg_participation_allow_overachievement") if hr.get("qorg_participation_allow_overachievement") is not None else 1,
        "prevent_start_with_pending_clearance":hr.get("qorg_participation_block_pending_clearance") if hr.get("qorg_participation_block_pending_clearance") is not None else 1,
        "require_final_evaluation":hr.get("qorg_participation_require_final") if hr.get("qorg_participation_require_final") is not None else 1,
    }
    return frappe._dict(values)
def validate_weighted_rows(rows,label):
    if not rows:return
    total=sum(flt(r.weight) for r in rows)
    if abs(total-100)>0.01:
        diff=100-total;frappe.throw(_("{0} weights must total 100%. Current total: {1}%. Required adjustment: {2}{3}%.").format(label,total,"add " if diff>0 else "remove ",abs(diff)))
def validate_opportunity(doc,method=None):
    if doc.get("qorg_participation_type"):
        if cint(doc.get("qorg_number_of_positions"))<1:frappe.throw(_("Number of Positions must be at least 1."))
        sw=flt(doc.get("qorg_screening_weight"));aw=flt(doc.get("qorg_assessment_weight"))
        if abs(sw+aw-100)>0.01:frappe.throw(_("Screening and Assessment weights must total exactly 100%. Current total: {0}%.").format(sw+aw))
        validate_weighted_rows(doc.get("qorg_assessment_plan") or [],_("Assessment stage"))
def validate_application(doc,method=None):
    prevent_duplicate_application(doc);validate_unique_priority(doc);validate_screening(doc)
    if doc.available_from and doc.available_to and getdate(doc.available_to)<getdate(doc.available_from):frappe.throw(_("Available To cannot be before Available From."))
    if doc.final_decision and settings().require_decision_rationale and not (doc.decision_rationale or "").strip():frappe.throw(_("Decision Rationale is required."))
    if doc.final_decision and not doc.decision_on:doc.decision_on=now_datetime();doc.decision_by=frappe.session.user
def load_assessment_stage(doc):
    if not doc.application:return
    app=frappe.get_doc("Participation Application",doc.application);doc.opportunity=app.opportunity
    stage=frappe.db.get_value("Participation Assessment Stage",{"parent":app.opportunity,"parenttype":"External Opportunity","parentfield":"qorg_assessment_plan","sequence":doc.stage_sequence},["stage_name","assessment_method","passing_score","allow_retry","maximum_attempts","retry_requires_approval"],as_dict=True)
    if stage:
        for field in stage:
            if doc.meta.has_field(field) and not doc.get(field):doc.set(field,stage[field])
def validate_assessment(doc,method=None):
    load_assessment_stage(doc)
    if doc.status=="Completed":
        if doc.score is None:frappe.throw(_("Score is required for a completed assessment."))
        passing=frappe.db.get_value("Participation Assessment Stage",{"parent":doc.opportunity,"sequence":doc.stage_sequence},"passing_score") or 60
        doc.result="Passed" if flt(doc.score)>=flt(passing) else "Failed"
def recalculate_application(application):
    app=frappe.get_doc("Participation Application",application);opp=frappe.get_doc("External Opportunity",app.opportunity)
    stages=opp.get("qorg_assessment_plan") or [];scores=[];weighted=0;weight=0
    for stage in stages:
        attempts=frappe.get_all("Participation Assessment",filters={"application":app.name,"stage_sequence":stage.sequence,"status":["!=","Cancelled"]},fields=["score","status","result","attempt_number"],order_by="attempt_number asc")
        current=attempts[-1] if attempts else None
        if current and current.status=="Completed":weighted+=flt(current.score)*flt(stage.weight);weight+=flt(stage.weight);scores.append(current)
    assessment=flt(weighted/weight,2) if weight else 0;overall=flt(flt(app.screening_score)*flt(opp.qorg_screening_weight)/100+assessment*flt(opp.qorg_assessment_weight)/100,2)
    frappe.db.set_value("Participation Application",app.name,{"assessment_score":assessment,"overall_score":overall},update_modified=False);rank_applications(app.opportunity)
def rank_applications(opportunity):
    rows=frappe.get_all("Participation Application",filters={"opportunity":opportunity,"status":["not in",["Withdrawn","Cancelled"]]},fields=["name"],order_by="overall_score desc, creation asc")
    for i,row in enumerate(rows,1):frappe.db.set_value("Participation Application",row.name,"ranking",i,update_modified=False)
def validate_engagement(doc,method=None):
    if doc.start_date and doc.end_date and getdate(doc.end_date)<getdate(doc.start_date):frappe.throw(_("End Date cannot be before Start Date."))
    s=settings()
    if doc.status=="Active" and s.prevent_start_with_pending_clearance:
        if doc.safeguarding_clearance_status=="Pending" or doc.background_check_status=="Pending":frappe.throw(_("Required clearances must be completed before activation."))
    rows=doc.get("onboarding_activities") or [];doc.onboarding_completion=flt(sum(1 for r in rows if r.status in ("Completed","Waived"))*100/len(rows),2) if rows else 0
    if doc.status=="Completed" and s.require_final_evaluation and not doc.final_rating:frappe.throw(_("Final Rating is required before completion."))
def validate_service_log(doc,method=None):
    s=settings()
    if flt(doc.hours)<=0:frappe.throw(_("Hours must be greater than zero."))
    if flt(doc.hours)>flt(s.maximum_hours_per_day):frappe.throw(_("Hours exceed the maximum allowed per day."))
    if s.require_service_log_evidence and not doc.evidence:frappe.throw(_("Evidence is required."))
    if doc.status=="Rejected" and not (doc.rejection_reason or "").strip():frappe.throw(_("Rejection Reason is required."))
def update_verified_hours(engagement):
    total=frappe.db.sql("select coalesce(sum(hours),0) from `tabParticipation Service Log` where engagement=%s and status='Verified'",engagement)[0][0]
    frappe.db.set_value("Participation Engagement",engagement,"completed_hours",total,update_modified=False)


def prevent_duplicate_application(doc):
    active=["Draft","Under Screening","Screened In","Under Assessment","Selected","Reserve / Waitlisted"]
    duplicate=frappe.db.get_value("Participation Application",{"external_person":doc.external_person,"opportunity":doc.opportunity,"status":["in",active],"name":["!=",doc.name or ""]},"name")
    if duplicate:frappe.throw(_("An active application already exists: {0}").format(duplicate))
def validate_unique_priority(doc):
    if doc.final_decision in ("Selected","Reserve / Waitlisted") and cint(doc.selection_priority)<=0:frappe.throw(_("Selection Priority is required."))
    if cint(doc.selection_priority)>0:
        duplicate=frappe.db.get_value("Participation Application",{"opportunity":doc.opportunity,"selection_priority":doc.selection_priority,"final_decision":["in",["Selected","Reserve / Waitlisted"]],"name":["!=",doc.name or ""]},"name")
        if duplicate:frappe.throw(_("Selection Priority is already used by {0}.").format(duplicate))
def validate_screening(doc):
    rows=doc.get("screening_criteria") or [];weighted=0;weight=0
    for row in rows:
        if row.mandatory and row.result=="Not Met":doc.screening_score=0;return
        if row.result in ("Met","Not Met"):
            value=100 if row.result=="Met" else 0;weighted+=value*flt(row.weight);weight+=flt(row.weight)
        elif row.score is not None:weighted+=flt(row.score)*flt(row.weight);weight+=flt(row.weight)
    doc.screening_score=flt(weighted/weight,2) if weight else 0
