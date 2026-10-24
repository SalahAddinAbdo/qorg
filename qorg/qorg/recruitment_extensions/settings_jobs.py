import frappe
from frappe.utils import getdate, today
from .settings import get_settings

def run_daily_recruitment_settings_jobs():
    s=get_settings()
    if not s.automatically_expire_offers or not frappe.db.exists("DocType","Job Offer"): return
    if not frappe.get_meta("Job Offer").has_field("qorg_valid_until"): return
    names=frappe.get_all("Job Offer",filters={"qorg_response_status":["in",["Draft","Issued"]],"qorg_valid_until":["<",today()]},pluck="name")
    for name in names:
        frappe.db.set_value("Job Offer",name,{"qorg_response_status":"Expired","qorg_response_date":today()},update_modified=False)
        applicant=frappe.db.get_value("Job Offer",name,"qorg_job_applicant")
        if applicant: frappe.db.set_value("Job Applicant",applicant,{"qorg_selection_status":"Expired","qorg_next_action":"Proceed with next ranked candidate"},update_modified=False)
