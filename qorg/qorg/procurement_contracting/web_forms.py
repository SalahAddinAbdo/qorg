from __future__ import annotations
import frappe
from frappe import _

LAYOUT_TYPES = {"Page Break", "Section Break", "Column Break"}

def section(label): return {"fieldtype":"Section Break","label":label}
def column(): return {"fieldtype":"Column Break"}
def page(label): return {"fieldtype":"Page Break","label":label}
def field(fieldname, required=False, read_only=False, label=None): return {"fieldname":fieldname,"required":required,"read_only":read_only,"label":label}

WEB_FORMS = [
 {
  "title":"Supplier Registration","route":"supplier-registration","doc_type":"Supplier Registration",
  "allow_multiple":0,"allow_edit":1,"show_list":0,"allow_print":1,"key_required":0,
  "introduction_text":"Create and maintain one supplier profile for procurement opportunities. Approved profiles may be locked and updated only through a controlled request.",
  "success_message":"Your supplier profile has been saved successfully.","submit_button_label":"Save Supplier Profile",
  "layout":[
   section("Legal Identity"),field("legal_name",True),field("country"),column(),field("registration_number"),field("tax_id"),
   section("Contact Details"),field("email",True),column(),
   page("Documents and Declarations"),section("Supporting Documents"),field("documents"),section("Declarations"),field("declarations"),
   page("Bank Information"),section("Settlement Account"),field("bank_name"),field("account_name"),field("account_number"),column(),field("iban"),field("swift_code"),field("bank_currency"),field("bank_confirmation"),
   section("Review Status"),field("registration_status",read_only=True),field("risk_rating",read_only=True),column(),field("review_expiry_date",read_only=True),field("supplier",read_only=True)
  ]
 },
 {
  "title":"Tender Submission","route":"tender-submission","doc_type":"Procurement Submission",
  "allow_multiple":1,"allow_edit":1,"show_list":1,"allow_print":1,"key_required":1,
  "introduction_text":"Submit a protected offer for an open procurement process. Technical and financial files remain separate and submitted bids cannot be edited.",
  "success_message":"Your tender submission has been received successfully.","submit_button_label":"Submit Tender",
  "layout":[
   section("Opportunity and Supplier Profile"),field("procurement_process",True,True),field("procurement_notice",False,True),column(),field("supplier_registration",True),field("supplier",False,True),
   page("Technical Offer"),section("Technical Envelope"),field("technical_proposal",True),
   page("Financial Offer and Security"),section("Financial Envelope"),field("financial_proposal",True),column(),field("bid_security"),
   section("Confirmation"),field("profile_current_confirmation",True),field("declaration",True),
   section("Submission Status"),field("submission_status",False,True),field("submitted_at",False,True)
  ]
 }
]

def _set(row, meta, fieldname, value):
 if meta.has_field(fieldname): row.set(fieldname,value)

def _apply_settings(doc, definition):
 values={"title":definition["title"],"route":definition["route"],"doc_type":definition["doc_type"],"module":"QOrg","is_standard":0,"published":1,"login_required":1,"anonymous":0,"allow_multiple":definition["allow_multiple"],"allow_edit":definition["allow_edit"],"show_list":definition["show_list"],"allow_print":definition["allow_print"],"introduction_text":definition["introduction_text"],"success_message":definition["success_message"],"submit_button_label":definition["submit_button_label"]}
 for k,v in values.items():
  if doc.meta.has_field(k): doc.set(k,v)
 if doc.meta.has_field("key_required"): doc.key_required=definition["key_required"]
 # Inherit the same managed design architecture used by opportunity forms.
 for k,v in {"qorg_web_form_design_enabled":1,"qorg_inherit_global_web_form_design":1,"qorg_header_style":"Default"}.items():
  if doc.meta.has_field(k): doc.set(k,v)

def _rebuild_fields(doc, definition):
 table=next((f.fieldname for f in doc.meta.fields if f.fieldtype=="Table" and f.options=="Web Form Field"),None)
 if not table: frappe.throw(_("Web Form Field table was not found."))
 child_meta=frappe.get_meta(doc.meta.get_field(table).options); target_meta=frappe.get_meta(definition["doc_type"]); doc.set(table,[]); idx=0
 for item in definition["layout"]:
  row=doc.append(table,{})
  if item.get("fieldtype") in LAYOUT_TYPES:
   idx+=1; ft=item["fieldtype"]
   if ft!="Page Break": _set(row,child_meta,"fieldname",f"qorg_procurement_layout_{idx}")
   _set(row,child_meta,"fieldtype",ft); _set(row,child_meta,"label",item.get("label") or ""); continue
  target=target_meta.get_field(item["fieldname"])
  if not target: frappe.throw(_("{0} is missing managed field {1}").format(definition["doc_type"],item["fieldname"]))
  for k,v in {"fieldname":target.fieldname,"fieldtype":target.fieldtype,"label":item.get("label") or target.label or target.fieldname,"options":target.options,"description":target.description,"reqd":int(item.get("required",False)),"read_only":int(item.get("read_only",False))}.items(): _set(row,child_meta,k,v)
  if target.fieldtype=="Link": _set(row,child_meta,"allow_read_on_all_link_options",1)

def provision_procurement_web_forms():
 if not frappe.db.exists("DocType","Web Form"): return
 for definition in WEB_FORMS:
  name=frappe.db.get_value("Web Form",{"route":definition["route"]},"name"); doc=frappe.get_doc("Web Form",name) if name else frappe.new_doc("Web Form")
  _apply_settings(doc,definition); _rebuild_fields(doc,definition)
  if doc.meta.has_field("client_script"): doc.client_script=""
  doc.save(ignore_permissions=True) if name else doc.insert(ignore_permissions=True)
 frappe.clear_cache(doctype="Web Form")
