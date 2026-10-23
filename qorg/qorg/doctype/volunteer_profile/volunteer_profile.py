from frappe.model.document import Document
import frappe
from frappe.utils import getdate
class VolunteerProfile(Document):
    def validate(self):
        duplicate=frappe.db.get_value("Volunteer Profile",{"external_person":self.external_person,"name":("!=",self.name or "")},"name")
        if duplicate: frappe.throw(f"External Person is already linked to Volunteer Profile {duplicate}.")
        if self.available_from and self.available_until and getdate(self.available_until)<getdate(self.available_from): frappe.throw("Available Until cannot be before Available From.")
