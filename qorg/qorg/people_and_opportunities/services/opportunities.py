import frappe
from frappe.utils import getdate, today
from qorg.qorg.people_and_opportunities.type_service import behavior_code
def validate_opportunity(doc):
    if doc.closing_date and doc.opening_date and getdate(doc.closing_date)<getdate(doc.opening_date): frappe.throw("Closing Date cannot be before Opening Date.")
    if behavior_code(doc.opportunity_type)=="Employment" and not doc.job_opening: frappe.throw("Job Opening is required for Employment opportunities.")
    if doc.job_opening:
        duplicate=frappe.db.get_value("External Opportunity",{"job_opening":doc.job_opening,"name":("!=",doc.name or ""),"status":("not in",["Archived","Rejected"])},"name")
        if duplicate: frappe.throw(f"Job Opening is already linked to {duplicate}.")
    if doc.minimum_age and doc.maximum_age and doc.minimum_age>doc.maximum_age: frappe.throw("Minimum Age cannot exceed Maximum Age.")
    if doc.status=="Published" and getdate(doc.closing_date)<getdate(today()): frappe.throw("An expired opportunity cannot be published.")
    primaries=sum(1 for x in doc.locations or [] if x.is_primary)
    if primaries>1: frappe.throw("Only one location can be Primary.")
