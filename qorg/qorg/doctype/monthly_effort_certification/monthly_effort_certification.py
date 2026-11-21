import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt,getdate
from qorg.qorg.payroll_workforce_allocation.utils import stable_hash
class MonthlyEffortCertification(Document):
    def validate(self):
        if getdate(self.end_date)<getdate(self.start_date): frappe.throw(_("End Date cannot precede Start Date."))
        if flt(self.total_compensated_hours)<=0: frappe.throw(_("Total Compensated Hours must be greater than zero."))
        if not self.details: frappe.throw(_("At least one effort detail row is required."))
        total=sum(flt(x.hours) for x in self.details)
        if abs(total-flt(self.total_compensated_hours))>0.01: frappe.throw(_("Effort hours must equal Total Compensated Hours. Current total: {0}; required difference: {1}.").format(total,flt(self.total_compensated_hours)-total))
        for row in self.details: row.percentage=flt(row.hours/flt(self.total_compensated_hours)*100,8)
        if self.status not in ("Draft","Employee Certified","Supervisor Approved","Finance Verified","Locked","Cancelled"): frappe.throw(_("Invalid certification status."))
        duplicate=frappe.db.exists(self.doctype,{"employee":self.employee,"docstatus":1,"name":["!=",self.name],"start_date":["<=",self.end_date],"end_date":[">=",self.start_date]})
        if duplicate: frappe.throw(_("An overlapping submitted Monthly Effort Certification exists: {0}").format(duplicate))
        self.source_fingerprint=stable_hash({"employee":self.employee,"company":self.company,"start":self.start_date,"end":self.end_date,"hours":self.total_compensated_hours,"details":[x.as_dict() for x in self.details]})
    def before_submit(self):
        if self.status!="Finance Verified": frappe.throw(_("Finance verification is required before submission."))
    def on_submit(self): self.db_set("status","Locked",update_modified=False)
    def before_cancel(self):
        used=frappe.db.exists("Payroll Allocation Result",{"evidence_type":"Monthly Effort Certification","evidence_reference":self.name,"parenttype":"Payroll Allocation Run","docstatus":1})
        if used: frappe.throw(_("This certification is used by submitted Payroll Allocation Run {0} and cannot be cancelled.").format(used))
    def on_cancel(self): self.db_set("status","Cancelled",update_modified=False)
    def on_trash(self):
        used=frappe.db.exists("Payroll Allocation Result",{"evidence_type":"Monthly Effort Certification","evidence_reference":self.name})
        if self.docstatus or used: frappe.throw(_("Only an unused draft Monthly Effort Certification can be deleted."))
