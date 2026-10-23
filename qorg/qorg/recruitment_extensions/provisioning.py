from __future__ import annotations
import json
from pathlib import Path
import frappe
ROLES=("Recruitment User","Recruitment Manager")
REQUIRED=("Job Requisition","Job Opening","Job Applicant","Interview Type","Interview","Interview Feedback","Job Offer","Appointment Letter","Employee","Employee Onboarding","External Person","External Opportunity")
def _specs():return json.loads(Path(__file__).parent.joinpath("data","custom_fields.json").read_text())
def provision_recruitment_extensions():
    missing=[x for x in REQUIRED if not frappe.db.exists("DocType",x)]
    if missing:frappe.throw("Missing recruitment dependencies: "+", ".join(missing))
    for role in ROLES:
        if not frappe.db.exists("Role",role):frappe.get_doc({"doctype":"Role","role_name":role,"desk_access":1}).insert(ignore_permissions=True)
    for spec in _specs():
        if not frappe.db.exists("DocType",spec["dt"]):continue
        name=f"{spec['dt']}-{spec['fieldname']}";existing=frappe.db.exists("Custom Field",name)
        values={**spec,"doctype":"Custom Field","name":name,"is_system_generated":1,"module":"QOrg"}
        if not existing:frappe.get_doc(values).insert(ignore_permissions=True);continue
        doc=frappe.get_doc("Custom Field",name)
        if doc.fieldtype!=spec["fieldtype"] or (spec.get("options") and doc.options!=spec.get("options")):frappe.throw(f"Incompatible Custom Field {name}")
        for key,value in spec.items():
            if key not in {"dt","fieldname"}:doc.set(key,value)
        doc.is_system_generated=1;doc.module="QOrg";doc.flags.ignore_permissions=True;doc.save()
    _email_templates();
    from qorg.qorg.recruitment_extensions.migration import migrate_interview_round_extensions, reconcile_existing_recruitment, reconcile_selection_queue
    migrate_interview_round_extensions(); reconcile_existing_recruitment(); reconcile_selection_queue()
    frappe.clear_cache()
def _email_templates():
    templates=(("Recruitment Interview Invitation","Interview Invitation","Your interview has been scheduled. Please review the date and time shared by the recruitment team."),("Recruitment Offer Issued","Job Offer","A job offer has been issued for your review."),("Recruitment Application Decision","Application Update","Your application status has been updated."))
    for name,subject,response in templates:
        if not frappe.db.exists("Email Template",name):frappe.get_doc({"doctype":"Email Template","name":name,"subject":subject,"response":response}).insert(ignore_permissions=True)
