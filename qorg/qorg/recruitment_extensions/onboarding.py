import frappe
from frappe import _
from frappe.utils import flt, now_datetime
EDITABLE={"qorg_activity_status","qorg_completion_percent","qorg_completion_remarks","qorg_evidence_attachment"}

def _rows(doc): return doc.get("activities") or doc.get("boarding_activities") or []

def validate_onboarding(doc, method=None):
    old=doc.get_doc_before_save()
    if old and frappe.session.user!="Administrator" and "HR Manager" not in frappe.get_roles():
        oldmap={r.name:r for r in _rows(old) if r.name}
        for row in _rows(doc):
            prev=oldmap.get(row.name)
            if not prev: continue
            changed={f for f in row.as_dict() if row.get(f)!=prev.get(f) and not f.startswith("_")}
            if changed and row.get("qorg_assigned_user")!=frappe.session.user: frappe.throw(_("You may update only onboarding activities assigned to you."),frappe.PermissionError)
            if row.get("qorg_assigned_user")==frappe.session.user and changed-EDITABLE: frappe.throw(_("Assigned users may update only status, completion, remarks, and evidence."),frappe.PermissionError)
    total=0; count=0; mandatory_open=[]
    for r in _rows(doc):
        pct=min(max(flt(r.get("qorg_completion_percent")),0),100); total+=pct; count+=1
        if pct>=100 and not r.get("qorg_completed_on"): r.qorg_completed_on=now_datetime(); r.qorg_completed_by=frappe.session.user
        if r.get("qorg_is_mandatory") and pct<100: mandatory_open.append(r.get("activity_name") or r.get("activity"))
    if hasattr(doc,"qorg_completion_percent"): doc.qorg_completion_percent=flt(total/count,2) if count else 0
    if doc.get("status") in {"Completed","Complete"} and mandatory_open: frappe.throw(_("Mandatory onboarding activities remain incomplete: {0}").format(", ".join(filter(None,mandatory_open))))
