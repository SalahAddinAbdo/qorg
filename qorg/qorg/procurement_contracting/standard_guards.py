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
