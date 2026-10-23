import frappe
from frappe.utils import getdate
from qorg.qorg.people_and_opportunities.type_service import behavior_code
def validate_application(doc):
    opp=frappe.get_doc("External Opportunity",doc.external_opportunity)
    if behavior_code(opp.opportunity_type)!="Volunteering": frappe.throw("Volunteer Application requires a Volunteering opportunity.")
    if opp.status not in {"Published","Closed"} and doc.status!="Draft": frappe.throw("Applications can only be submitted to a published opportunity.")
    doc.company=opp.company
    person=frappe.get_doc("External Person",doc.external_person); doc.applicant_name=person.full_name; doc.email=person.primary_email; doc.mobile_no=person.mobile_no
    if doc.is_new() or doc.has_value_changed("external_person") or doc.has_value_changed("external_opportunity"):
        if not opp.allow_multiple_applications:
            duplicate=frappe.db.get_value("Volunteer Application",{"external_person":doc.external_person,"external_opportunity":doc.external_opportunity,"name":("!=",doc.name or ""),"status":("not in",["Withdrawn","Rejected","Closed"])},"name")
            if duplicate: frappe.throw(f"An active application already exists: {duplicate}.")
    if doc.availability_start_date and doc.availability_end_date and getdate(doc.availability_end_date)<getdate(doc.availability_start_date): frappe.throw("Availability end date cannot be before start date.")
    if not doc.screening_answers and opp.screening_questions:
        for q in opp.screening_questions: doc.append("screening_answers",{"question_reference":q.name,"question":q.question,"answer_type":q.answer_type})
