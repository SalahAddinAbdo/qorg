import frappe
from frappe.utils import today
from qorg.qorg.people_and_opportunities.settings import require_feature

def _doc(name):
 d=frappe.get_doc("Volunteer Application",name); require_feature("volunteer_management", d.company); d.check_permission("write"); return d
@frappe.whitelist(methods=["POST"])
def submit_application(name:str):
 d=_doc(name)
 if d.status!="Draft": frappe.throw("Only Draft applications can be submitted.")
 d.status="Submitted"; d.save(); return d.name
@frappe.whitelist(methods=["POST"])
def start_screening(name:str):
 d=_doc(name)
 if d.status not in {"Submitted","Under Screening"}: frappe.throw("Application is not ready for screening.")
 d.status="Under Screening"; d.screening_status="In Progress"; d.save(); return d.name
@frappe.whitelist(methods=["POST"])
def record_decision(name:str,decision:str,remarks:str):
 if decision not in {"Approved","Rejected","Waitlisted"}: frappe.throw("Invalid decision.")
 if "Volunteer Manager" not in frappe.get_roles() and frappe.session.user!="Administrator": frappe.throw("Volunteer Manager role is required.",frappe.PermissionError)
 d=_doc(name); d.final_decision=decision; d.decision_date=today(); d.decision_by=frappe.session.user; d.decision_remarks=remarks; d.status="Approved" if decision=="Approved" else "Rejected" if decision=="Rejected" else "Under Review"; d.save(); return d.name

@frappe.whitelist(methods=["POST"])
def convert_to_volunteer(name: str):
    if "Volunteer Manager" not in frappe.get_roles() and frappe.session.user != "Administrator":
        frappe.throw("Volunteer Manager role is required.", frappe.PermissionError)
    d=_doc(name)
    if d.status!="Approved": frappe.throw("Only Approved applications can be converted.")
    profile=frappe.db.get_value("Volunteer Profile",{"external_person":d.external_person},"name")
    if not profile:
        profile_doc=frappe.get_doc({"doctype":"Volunteer Profile","external_person":d.external_person,"company":d.company,"source_application":d.name,"coordinator":d.assigned_reviewer,"available_from":d.availability_start_date,"available_until":d.availability_end_date,"hours_per_week":d.hours_per_week,"preferred_arrangement":d.preferred_work_arrangement})
        profile_doc.insert(); profile=profile_doc.name
    engagement=frappe.get_doc({"doctype":"Volunteer Engagement","volunteer_profile":profile,"external_opportunity":d.external_opportunity,"company":d.company,"coordinator":d.assigned_reviewer,"role_title":frappe.db.get_value("External Opportunity",d.external_opportunity,"opportunity_title"),"start_date":d.availability_start_date or today(),"end_date":d.availability_end_date,"expected_hours_per_week":d.hours_per_week,"source_application":d.name,"status":"Draft"})
    engagement.insert(); d.volunteer=profile; d.volunteer_engagement=engagement.name; d.status="Converted"; d.save(); return {"volunteer_profile":profile,"volunteer_engagement":engagement.name}
