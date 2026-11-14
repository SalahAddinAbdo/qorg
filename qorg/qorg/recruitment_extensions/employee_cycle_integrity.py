from __future__ import annotations
import frappe
from frappe import _
from frappe.utils import getdate


def validate_work_commencement(doc, method=None):
    if doc.employee:
        employee = frappe.db.get_value("Employee", doc.employee, ["company", "designation", "department", "reports_to"], as_dict=True) or {}
        for fieldname in ("company", "designation", "department", "reports_to"):
            if doc.get(fieldname) and employee.get(fieldname) and doc.get(fieldname) != employee.get(fieldname):
                frappe.throw(_("{0} must match the linked Employee.").format(doc.meta.get_label(fieldname)))
    if doc.appointment_letter:
        appointment = frappe.get_doc("Appointment Letter", doc.appointment_letter)
        mapping = {"qorg_job_offer":"job_offer", "qorg_job_applicant":"job_applicant", "employee":"employee"}
        for source, target in mapping.items():
            if appointment.meta.has_field(source) and appointment.get(source) and doc.get(target) and appointment.get(source) != doc.get(target):
                frappe.throw(_("{0} must match the linked Appointment Letter.").format(doc.meta.get_label(target)))
    if doc.job_offer and doc.job_applicant:
        offer_applicant = frappe.db.get_value("Job Offer", doc.job_offer, "job_applicant")
        if offer_applicant and offer_applicant != doc.job_applicant:
            frappe.throw(_("Job Offer must belong to Job Applicant {0}.").format(doc.job_applicant))
    if doc.actual_commencement_date and doc.expected_joining_date and doc.status == "Commenced" and getdate(doc.actual_commencement_date) < getdate(doc.expected_joining_date):
        if not (doc.commencement_remarks or "").strip():
            frappe.throw(_("Commencement Remarks are required when Actual Commencement Date is before Expected Joining Date."))
    if doc.payroll_effective_date and doc.actual_commencement_date and getdate(doc.payroll_effective_date) < getdate(doc.actual_commencement_date):
        frappe.throw(_("Payroll Effective Date cannot be before Actual Commencement Date."))
    if doc.attendance_effective_date and doc.actual_commencement_date and getdate(doc.attendance_effective_date) < getdate(doc.actual_commencement_date):
        frappe.throw(_("Attendance Effective Date cannot be before Actual Commencement Date."))
    if doc.onboarding:
        onboarding_employee = frappe.db.get_value("Employee Onboarding", doc.onboarding, "employee")
        if onboarding_employee and doc.employee and onboarding_employee != doc.employee:
            frappe.throw(_("Employee Onboarding must belong to Employee {0}.").format(doc.employee))


def prevent_incomplete_employee_exit(doc, method=None):
    employee = doc.get("employee")
    if not employee:
        return
    open_custody = frappe.db.exists("Asset Custody", {"custodian": employee, "docstatus":["<",2], "custody_status":["in",["Pending Handover","Active","Return Due","Overdue"]]})
    if open_custody and not doc.get("custom_custody_exception_approved"):
        frappe.throw(_("Employee has active custody {0}.").format(open_custody))
    if frappe.db.exists("DocType", "Stock Handover"):
        pending_handover = frappe.db.exists("Stock Handover", {"recipient_employee": employee, "docstatus":["<",2], "handover_status":["in",["Draft","Pending Handover","Discrepancy Review"]]})
        if pending_handover:
            frappe.throw(_("Employee has pending Stock Handover {0}.").format(pending_handover))
