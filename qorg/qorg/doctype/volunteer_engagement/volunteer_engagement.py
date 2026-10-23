from frappe.model.document import Document
import frappe
from frappe.utils import getdate,today
from qorg.qorg.people_and_opportunities.type_service import behavior_code
class VolunteerEngagement(Document):
    def validate(self):
        if self.end_date and getdate(self.end_date)<getdate(self.start_date): frappe.throw("End Date cannot be before Start Date.")
        if self.external_opportunity:
            row=frappe.db.get_value("External Opportunity",self.external_opportunity,["opportunity_type","company"],as_dict=True)
            if not row or behavior_code(row.opportunity_type)!="Volunteering": frappe.throw("Volunteer Engagement requires a Volunteering opportunity.")
            if row.company!=self.company: frappe.throw("Company must match the linked opportunity.")
        if self.status=="Completed" and not self.completion_date: self.completion_date=today()
