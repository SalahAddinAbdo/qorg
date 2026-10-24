import frappe
from frappe import _
from frappe.utils import flt, now_datetime
from .settings import get_settings
EDITABLE={"qorg_activity_status","qorg_completion_percent","qorg_completion_remarks","qorg_evidence_attachment"}

def _rows(doc):
    return doc.get("activities") or doc.get("boarding_activities") or []

def validate_onboarding(doc, method=None):
    s=get_settings();old=doc.get_doc_before_save()
    if old and frappe.session.user!="Administrator" and "HR Manager" not in frappe.get_roles():
        oldmap={r.name:r for r in _rows(old) if r.name}
        for row in _rows(doc):
            prev=oldmap.get(row.name)
            if not prev: continue
            changed={f for f in row.as_dict() if row.get(f)!=prev.get(f) and not f.startswith("_")}
            assigned=row.get("qorg_assigned_user")==frappe.session.user
            if changed and not assigned:
                frappe.throw(_("You may update only onboarding activities assigned to you."),frappe.PermissionError)
            if assigned and changed-EDITABLE:
                frappe.throw(_("Assigned users may update only status, completion, remarks, and evidence."),frappe.PermissionError)
            if assigned and prev.get("qorg_activity_status")=="Completed" and row.get("qorg_activity_status")!="Completed" and not s.allow_assigned_user_reopen:
                frappe.throw(_("Only HR may reopen a completed onboarding activity."),frappe.PermissionError)
    total=0;count=0;mandatory_open=[]
    for row in _rows(doc):
        pct=min(max(flt(row.get("qorg_completion_percent")),0),100);row.qorg_completion_percent=pct;total+=pct;count+=1
        if s.require_mandatory_activity_evidence and row.get("qorg_is_mandatory"): row.qorg_requires_evidence=1
        if pct>=100:
            if row.get("qorg_requires_evidence") and not row.get("qorg_evidence_attachment"):
                frappe.throw(_("Evidence is required for completed activity: {0}").format(row.get("activity_name") or row.get("activity") or row.idx))
            if not row.get("qorg_completed_on"): row.qorg_completed_on=now_datetime();row.qorg_completed_by=frappe.session.user
            if s.require_activity_verification and not row.get("qorg_verified_by"):
                row.qorg_activity_status="Submitted for Verification"
        if row.get("qorg_is_mandatory") and pct<100: mandatory_open.append(row.get("activity_name") or row.get("activity") or str(row.idx))
    if doc.meta.has_field("qorg_completion_percent"): doc.qorg_completion_percent=flt(total/count,2) if count else 0
    if s.require_mandatory_onboarding and doc.get("status") in {"Completed","Complete"} and mandatory_open:
        frappe.throw(_("Mandatory onboarding activities remain incomplete: {0}").format(", ".join(mandatory_open)))
