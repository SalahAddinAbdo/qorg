import frappe
from frappe.utils import now
from qorg.qorg.people_and_opportunities.settings import require_feature, settings
ALLOWED={"Draft":{"Under Review"},"Under Review":{"Approved","Rejected","Draft"},"Approved":{"Published","Draft"},"Published":{"Closed","Approved"},"Closed":{"Archived"},"Rejected":{"Draft"}}
@frappe.whitelist(methods=["POST"])
def transition_opportunity(name:str,status:str):
    doc=frappe.get_doc("External Opportunity",name); require_feature("public_opportunities", doc.company); doc.check_permission("write")
    if status=="Published" and settings().require_opportunity_approval and doc.status!="Approved": frappe.throw("Approval is required before publication.")
    if status not in ALLOWED.get(doc.status,set()): frappe.throw(f"Transition from {doc.status} to {status} is not allowed.")
    if status in {"Approved","Published","Closed","Archived","Rejected"} and "Opportunity Manager" not in frappe.get_roles() and frappe.session.user!="Administrator": frappe.throw("Opportunity Manager role is required.",frappe.PermissionError)
    doc.status=status
    if status=="Published": doc.published_on=now()
    doc.save(); return doc.name
