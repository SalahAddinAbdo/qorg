import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, now_datetime

class WorkCommencementNotice(Document):
    def validate(self):
        self._load_source_context()
        if self.status == "Commenced" and not self.actual_commencement_date:
            frappe.throw(_("Actual Commencement Date is required when status is Commenced."))
        if self.actual_commencement_date and self.expected_joining_date and getdate(self.actual_commencement_date) < getdate(self.expected_joining_date):
            frappe.msgprint(_("Actual Commencement Date is earlier than the expected date."), indicator="orange")
        if self.status in {"Deferred","No Show"} and not (self.delay_no_show_reason or "").strip():
            frappe.throw(_("Delay / No-show Reason is required."))

    def before_submit(self):
        if self.status != "Commenced": frappe.throw(_("Only a Commenced notice can be submitted."))
        self.hr_verified_by=frappe.session.user;self.hr_verification_date=now_datetime()

    def on_submit(self):
        employee=frappe.get_doc("Employee",self.employee)
        if not employee.date_of_joining: frappe.db.set_value("Employee",employee.name,"date_of_joining",self.actual_commencement_date,update_modified=False)
        if employee.meta.has_field("qorg_work_commencement_notice"): frappe.db.set_value("Employee",employee.name,"qorg_work_commencement_notice",self.name,update_modified=False)
        if self.job_applicant: frappe.db.set_value("Job Applicant",self.job_applicant,{"qorg_selection_status":"Employment Commenced","qorg_next_action":"Complete Employee Onboarding"},update_modified=False)

    def on_cancel(self):
        if self.job_applicant: frappe.db.set_value("Job Applicant",self.job_applicant,{"qorg_selection_status":"Appointment Issued","qorg_next_action":"Confirm Work Commencement"},update_modified=False)

    def _load_source_context(self):
        if not self.appointment_letter:return
        al=frappe.get_doc("Appointment Letter",self.appointment_letter)
        for field in ("qorg_job_offer","qorg_job_applicant","qorg_project","qorg_branch","qorg_cost_center","qorg_expected_joining_date"):
            target={"qorg_job_offer":"job_offer","qorg_job_applicant":"job_applicant","qorg_project":"project","qorg_branch":"branch","qorg_cost_center":"cost_center","qorg_expected_joining_date":"expected_joining_date"}[field]
            if not self.get(target) and al.meta.has_field(field): self.set(target,al.get(field))
        if self.employee:
            emp=frappe.get_doc("Employee",self.employee)
            for field in ("company","designation","department","reports_to"):
                if not self.get(field):self.set(field,emp.get(field))
