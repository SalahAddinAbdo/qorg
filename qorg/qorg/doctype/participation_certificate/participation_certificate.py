import frappe
from frappe import _
from frappe.model.document import Document
class ParticipationCertificate(Document):
    def validate(self):
        if self.engagement:
            e=frappe.get_doc("Participation Engagement",self.engagement)
            if e.status!="Completed":frappe.throw(_("Certificate can be issued only for a completed engagement."))
            for field in ("external_person","participation_type","role_title","start_date","end_date"):
                if not self.get(field):self.set(field,e.get(field))
            self.hours_completed=e.completed_hours
        if self.status=="Revoked" and not (self.revocation_reason or "").strip():frappe.throw(_("Revocation Reason is required."))
