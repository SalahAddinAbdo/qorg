from __future__ import annotations
import frappe
from qorg.qorg.people_and_opportunities.services.people import get_or_create_external_person
LEGACY_ALIASES={"custom_external_person":"qorg_external_person","custom_external_opportunity":"qorg_external_opportunity","custom_screening_status":"qorg_screening_status","custom_final_decision":"qorg_final_decision"}
def execute():
    from qorg.qorg.recruitment_extensions.provisioning import provision_recruitment_extensions
    provision_recruitment_extensions();reconcile_existing_recruitment();adopt_legacy_values();reconcile_selection_queue()
def reconcile_existing_recruitment():
    if not frappe.db.exists("Custom Field","Job Applicant-qorg_external_person"):return
    meta=frappe.get_meta("Job Applicant");email="email_id" if meta.has_field("email_id") else "email";phone="phone_number" if meta.has_field("phone_number") else "mobile_number"
    fields=["name","applicant_name",email,phone]
    for row in frappe.get_all("Job Applicant",filters={"qorg_external_person":["is","not set"]},fields=fields,limit_page_length=0):
        try:
            person=get_or_create_external_person({"full_name":row.applicant_name,"primary_email":row.get(email),"mobile_no":row.get(phone)},"Migration","Job Applicant",row.name)
            frappe.db.set_value("Job Applicant",row.name,"qorg_external_person",person.name,update_modified=False)
        except Exception:frappe.log_error(frappe.get_traceback(),f"Recruitment reconciliation failed: {row.name}")
def adopt_legacy_values():
    meta=frappe.get_meta("Job Applicant")
    for old,new in LEGACY_ALIASES.items():
        if not meta.has_field(old) or not meta.has_field(new):continue
        rows=frappe.get_all("Job Applicant",filters={new:["is","not set"],old:["is","set"]},fields=["name",old],limit_page_length=0)
        for row in rows:frappe.db.set_value("Job Applicant",row.name,new,row.get(old),update_modified=False)

def reconcile_selection_queue():
    if not frappe.db.exists("Custom Field","Job Applicant-qorg_selection_status"):return
    for row in frappe.get_all("Job Applicant",filters={"qorg_final_decision":["is","set"],"qorg_selection_status":["is","not set"]},fields=["name","qorg_final_decision","qorg_rank"],limit_page_length=0):
        status="Primary Candidate" if row.qorg_final_decision=="Selected" and int(row.qorg_rank or 0)==1 else "Reserve Candidate" if row.qorg_final_decision in {"Selected","Reserve / Waitlisted"} else "Closed"
        frappe.db.set_value("Job Applicant",row.name,{"qorg_selection_priority":row.qorg_rank,"qorg_selection_status":status},update_modified=False)
