from __future__ import annotations
import frappe
from qorg.qorg.people_and_opportunities.type_service import behavior_code
from qorg.qorg.people_and_opportunities.services.people import get_or_create_external_person

def validate_job_opening(doc, method=None):
    opportunity = getattr(doc, "qorg_external_opportunity", None)
    if opportunity:
        linked = frappe.db.get_value("External Opportunity", opportunity, ["opportunity_type","job_opening"], as_dict=True)
        if not linked or behavior_code(linked.opportunity_type) != "Employment":
            frappe.throw("Job Opening can only link to an Employment opportunity.")
        if linked.job_opening and linked.job_opening != doc.name:
            frappe.throw("The External Opportunity is linked to another Job Opening.")

def sync_job_applicant_person(doc, method=None):
    if getattr(doc, "qorg_external_person", None): return
    email = getattr(doc, "email_id", None) or getattr(doc, "email", None)
    mobile = getattr(doc, "phone_number", None) or getattr(doc, "mobile_number", None)
    full_name = getattr(doc, "applicant_name", None)
    if not full_name: return
    person = get_or_create_external_person({"full_name":full_name,"primary_email":email,"mobile_no":mobile},"Job Application","Job Applicant",doc.name)
    if doc.is_new():
        doc.qorg_external_person = person.name
    elif doc.qorg_external_person != person.name:
        doc.db_set("qorg_external_person", person.name, update_modified=False)

