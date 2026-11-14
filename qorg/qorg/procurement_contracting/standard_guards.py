import frappe
from frappe import _
from qorg.qorg.procurement_contracting.actions import validate_standard_buying_action

def _material_requests(doc):
 names=set()
 for row in getattr(doc,"items",[]) or []:
  for fieldname in ("material_request","material_request_no"):
   value=getattr(row,fieldname,None)
   if value:names.add(value)
 return names

def validate_rfq(doc,method=None):
 validate_rfq_extensions(doc)
 for name in _material_requests(doc):validate_standard_buying_action(name,"Create RFQ")

def validate_purchase_order(doc,method=None):
 for name in _material_requests(doc):validate_standard_buying_action(name,"Create Purchase Order")

def validate_contract_links(doc,method=None):
 contract=getattr(doc,"custom_procurement_contract",None)
 if not contract:return
 c=frappe.get_doc("Procurement Contract",contract)
 if c.status not in ("Active","Completed"):frappe.throw(_("The linked Procurement Contract must be active."))
 if getattr(doc,"company",None)!=c.company:frappe.throw(_("Company must match the Procurement Contract."))
 if getattr(doc,"currency",None) and doc.currency!=c.currency:frappe.throw(_("Currency must match the Procurement Contract."))


def validate_rfq_extensions(doc):
    from frappe.utils import cint, flt, now_datetime
    if getattr(doc, "custom_contact_employee", None):
        employee = frappe.db.get_value("Employee", doc.custom_contact_employee, ["employee_name", "designation", "cell_number", "company_email", "personal_email", "user_id"], as_dict=True) or {}
        doc.custom_contact_name = employee.get("employee_name")
        doc.custom_contact_designation = employee.get("designation")
        doc.custom_contact_phone = doc.custom_contact_phone or employee.get("cell_number")
        doc.custom_contact_email = doc.custom_contact_email or employee.get("company_email") or employee.get("personal_email") or employee.get("user_id")
    if doc.docstatus == 1:
        for fieldname in ("custom_submission_deadline", "custom_contact_name", "custom_contact_email", "custom_delivery_location"):
            if not doc.get(fieldname):
                frappe.throw(_("{0} is required before submission.").format(doc.meta.get_label(fieldname)))
    if doc.custom_submission_deadline and doc.custom_submission_deadline <= now_datetime() and doc.docstatus == 0:
        frappe.throw(_("Submission Deadline must be in the future."))
    if doc.custom_offer_validity_days is not None and cint(doc.custom_offer_validity_days) < 1:
        frappe.throw(_("Offer Validity Days must be at least 1."))
    if doc.custom_bid_security_required and (flt(doc.custom_bid_security_amount) <= 0 or cint(doc.custom_bid_security_validity) < 1):
        frappe.throw(_("Complete valid bid security amount and validity."))
    if doc.custom_site_visit_required and (not doc.custom_site_visit_datetime or not doc.custom_site_visit_location):
        frappe.throw(_("Site Visit Date, Time and Location are required."))
