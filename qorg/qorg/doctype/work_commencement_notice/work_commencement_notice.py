import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, now_datetime


class WorkCommencementNotice(Document):
    def validate(self):
        self._load_source_context()
        if self.status == "Commenced":
            if not self.actual_commencement_date:
                frappe.throw(_("Actual Commencement Date is required."))
            if not self.supervisor_confirmed_by:
                frappe.throw(_("Supervisor confirmation is required."))
        if self.status in {"Deferred", "No Show"} and not (self.delay_no_show_reason or "").strip():
            frappe.throw(_("Delay / No-show Reason is required."))
        if self.actual_commencement_date and self.expected_joining_date and self.status == "Commenced":
            if getdate(self.actual_commencement_date) < getdate(self.expected_joining_date) and not (self.commencement_remarks or "").strip():
                frappe.throw(_("Commencement Remarks are required when Actual Commencement Date is before Expected Joining Date."))

    def before_submit(self):
        if self.status != "Commenced":
            frappe.throw(_("Only a Commenced notice can be submitted."))
        from qorg.qorg.employee_lifecycle.service import prepare_commencement
        prepare_commencement(self)
        self.hr_verified_by = frappe.session.user
        self.hr_verification_date = now_datetime()

    def on_submit(self):
        from qorg.qorg.employee_lifecycle.service import finalize_commencement
        finalize_commencement(self)

    def on_cancel(self):
        # Never delete or roll back Employee/Contract records automatically. They may already
        # have downstream payroll, attendance or onboarding activity.
        if self.job_applicant and frappe.db.exists("Job Applicant", self.job_applicant):
            meta = frappe.get_meta("Job Applicant")
            values = {}
            if meta.has_field("qorg_selection_status"):
                values["qorg_selection_status"] = "Appointment Issued"
            if meta.has_field("qorg_next_action"):
                values["qorg_next_action"] = "Review cancelled commencement and linked lifecycle records"
            if values:
                frappe.db.set_value("Job Applicant", self.job_applicant, values, update_modified=False)

    def _load_source_context(self):
        if not self.appointment_letter:
            return
        appointment = frappe.get_doc("Appointment Letter", self.appointment_letter)
        mapping = {
            "qorg_job_offer": "job_offer",
            "qorg_job_applicant": "job_applicant",
            "qorg_project": "project",
            "qorg_branch": "branch",
            "qorg_cost_center": "cost_center",
            "qorg_expected_joining_date": "expected_joining_date",
        }
        for source, target in mapping.items():
            if not self.get(target) and appointment.meta.has_field(source):
                self.set(target, appointment.get(source))
        if self.employee and frappe.db.exists("Employee", self.employee):
            employee = frappe.get_doc("Employee", self.employee)
            for fieldname in ("company", "designation", "department", "reports_to"):
                if not self.get(fieldname):
                    self.set(fieldname, employee.get(fieldname))
