from __future__ import annotations
import frappe
from frappe import _
from frappe.utils import getdate


def _same(field, left, right, label):
    if left and right and left != right:
        frappe.throw(_("{0} does not match the linked record.").format(label))


def validate_participation_record(doc, method=None):
    person = doc.get("external_person")
    opportunity = doc.get("opportunity") or doc.get("external_opportunity")
    engagement_name = doc.get("engagement")
    application_name = doc.get("application")
    if person and not frappe.db.exists("External Person", person):
        frappe.throw(_("External Person does not exist."))
    if opportunity and not frappe.db.exists("External Opportunity", opportunity):
        frappe.throw(_("External Opportunity does not exist."))
    if application_name:
        application = frappe.db.get_value("Participation Application", application_name, ["external_person", "opportunity"], as_dict=True)
        if application:
            _same("external_person", person, application.external_person, _("External Person"))
            _same("opportunity", opportunity, application.opportunity, _("External Opportunity"))
    if engagement_name:
        engagement = frappe.db.get_value("Participation Engagement", engagement_name, ["external_person", "opportunity", "start_date", "end_date"], as_dict=True)
        if engagement:
            _same("external_person", person, engagement.external_person, _("External Person"))
            _same("opportunity", opportunity, engagement.opportunity, _("External Opportunity"))
            service_date = doc.get("service_date")
            if service_date and engagement.start_date and getdate(service_date) < getdate(engagement.start_date):
                frappe.throw(_("Service Date cannot be before Engagement Start Date."))
            if service_date and engagement.end_date and getdate(service_date) > getdate(engagement.end_date):
                frappe.throw(_("Service Date cannot be after Engagement End Date."))


def validate_volunteer_record(doc, method=None):
    person = doc.get("external_person")
    opportunity = doc.get("external_opportunity")
    if person and not frappe.db.exists("External Person", person):
        frappe.throw(_("External Person does not exist."))
    if opportunity and not frappe.db.exists("External Opportunity", opportunity):
        frappe.throw(_("External Opportunity does not exist."))
    if doc.doctype == "Volunteer Engagement" and opportunity:
        company = frappe.db.get_value("External Opportunity", opportunity, "company")
        _same("company", doc.get("company"), company, _("Company"))
