from __future__ import annotations
import frappe
from frappe import _
from frappe.utils import getdate


def validate_external_person_links(doc, method=None):
    if doc.contact and frappe.db.exists("Contact", doc.contact):
        email = frappe.db.get_value("Contact Email", {"parent": doc.contact, "is_primary": 1}, "email_id")
        if email and doc.primary_email and email.strip().lower() != doc.primary_email.strip().lower():
            frappe.throw(_("Primary Email must match the linked primary Contact email."))
    if doc.data_retention_until and doc.date_of_birth and getdate(doc.data_retention_until) <= getdate(doc.date_of_birth):
        frappe.throw(_("Data Retention Until must be after Date of Birth."))


def validate_external_opportunity_links(doc, method=None):
    if doc.project and frappe.db.exists("Project", doc.project):
        project_company = frappe.db.get_value("Project", doc.project, "company")
        if doc.company and project_company and doc.company != project_company:
            frappe.throw(_("External Opportunity Company must match the linked Project company."))
    if doc.start_date and doc.end_date and getdate(doc.end_date) < getdate(doc.start_date):
        frappe.throw(_("End Date cannot be before Start Date."))
    if doc.opening_date and doc.closing_date and getdate(doc.closing_date) < getdate(doc.opening_date):
        frappe.throw(_("Closing Date cannot be before Opening Date."))


def validate_job_applicant_person(doc, method=None):
    person = doc.get("qorg_external_person")
    if not person:
        return
    if not frappe.db.exists("External Person", person):
        frappe.throw(_("Linked External Person does not exist."))
    person_email = (frappe.db.get_value("External Person", person, "primary_email") or "").strip().lower()
    applicant_email = (doc.get("email_id") or "").strip().lower()
    if person_email and applicant_email and person_email != applicant_email:
        frappe.throw(_("Job Applicant email must match the linked External Person primary email."))
