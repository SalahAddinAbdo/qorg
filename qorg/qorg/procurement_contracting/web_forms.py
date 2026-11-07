from __future__ import annotations
import frappe


def section(label): return {"fieldtype":"Section Break","label":label}
def column(): return {"fieldtype":"Column Break"}
def page(label): return {"fieldtype":"Page Break","label":label}
def field(fieldname, required=False, read_only=False, label=None): return {"fieldname":fieldname,"required":required,"read_only":read_only,"label":label}

WEB_FORMS=[
 {"title":"Supplier Registration","route":"supplier-registration","doc_type":"Supplier Registration","allow_multiple":0,"allow_edit":1,"show_list":0,"allow_print":1,"key_required":0,
  "introduction_text":"Complete the supplier profile in full. Information is used for eligibility, due diligence, tendering, contracting and payment controls.","success_message":"Your supplier profile has been saved successfully.","submit_button_label":"Save Supplier Profile",
  "layout":[
   page("Organization"),section("Legal Identity"),field("legal_name",True),field("trade_name"),column(),field("supplier_type",True),field("country",True),section("Registration Details"),field("registration_number",True),field("tax_id"),column(),field("year_established"),field("employee_count"),
   page("Contact and Address"),section("Registered Address"),field("address_line_1",True),field("address_line_2"),field("city",True),column(),field("phone",True),field("email",True),field("website"),section("Primary Contact"),field("contact_person",True),field("contact_designation"),column(),field("contact_phone",True),field("contact_email",True),
   page("Capabilities"),section("Business Capability"),field("business_sectors",True),field("geographic_coverage"),section("Experience and Past Performance"),field("experience_summary"),
   page("Documents"),section("Mandatory and Supporting Documents"),field("registration_certificate",True),field("tax_certificate"),column(),field("licenses_certificates"),field("company_profile"),field("references_document"),field("documents"),
   page("Compliance"),section("Supplier Declarations"),field("conflict_of_interest",True),field("sanctions_declaration",True),column(),field("anti_fraud_declaration",True),field("data_consent",True),section("Additional Declaration"),field("declarations"),
   page("Bank Information"),section("Settlement Account"),field("bank_name"),field("account_name"),field("account_number"),column(),field("iban"),field("swift_code"),field("bank_currency"),field("bank_confirmation"),
   page("Review"),section("Profile Review Status"),field("registration_status",read_only=True),field("risk_rating",read_only=True),column(),field("review_expiry_date",read_only=True),field("supplier",read_only=True)]},
 {"title":"Tender Submission","route":"tender-submission","doc_type":"Procurement Submission","allow_multiple":1,"allow_edit":1,"show_list":1,"allow_print":1,"key_required":0,"login_required":1,
  "introduction_text":"Submit a protected tender for the selected opportunity. Keep the supplier profile current and upload technical and financial proposals separately.","success_message":"Your tender submission has been saved successfully.","submit_button_label":"Save Tender Submission",
  "layout":[
   page("Opportunity"),section("Opportunity and Supplier"),field("procurement_process",True,True),field("procurement_notice",read_only=True),column(),field("supplier_registration",True,True),field("supplier",True,True),
   page("Technical Offer"),section("Technical Proposal"),field("technical_proposal",True),
   page("Financial Offer"),section("Financial Proposal and Security"),field("financial_proposal",True),column(),field("bid_security"),
   page("Confirmation"),section("Supplier Profile Confirmation"),field("profile_current_confirmation",True),field("profile_confirmation_on",read_only=True),section("Declaration"),field("declaration",True),
   page("Submission Status"),section("Status and Version"),field("submission_status",read_only=True),field("submission_version",read_only=True),column(),field("submitted_at",read_only=True),field("supersedes_submission",read_only=True),section("Withdrawal"),field("withdrawn_on",read_only=True),field("withdrawal_reason",read_only=True)]}
]

def _set(doc,field,value):
 if doc.meta.has_field(field): setattr(doc,field,value)

def _apply_settings(doc,d):
 for k in ("title","route","doc_type","allow_multiple","allow_edit","show_list","allow_print","key_required","login_required","introduction_text","success_message","submit_button_label"):
  if k in d:_set(doc,k,d[k])
 for k,v in {"published":1,"is_standard":0,"qorg_web_form_design_enabled":1,"qorg_inherit_global_web_form_design":1,"qorg_header_style":"Default","qorg_web_form_design_version":"3.0.0"}.items():_set(doc,k,v)
 if doc.meta.has_field("custom_css"):doc.custom_css=""

def _rebuild_fields(doc,d):
 doc.set("web_form_fields",[]);meta=frappe.get_meta(d["doc_type"])
 for item in d["layout"]:
  row=doc.append("web_form_fields",{})
  if item.get("fieldtype") in {"Page Break","Section Break","Column Break"}:
   row.fieldtype=item["fieldtype"];row.label=item.get("label") or "";continue
  df=meta.get_field(item["fieldname"])
  if not df:frappe.throw(f"Missing field {d['doc_type']}.{item['fieldname']}")
  row.fieldname=df.fieldname;row.fieldtype=df.fieldtype;row.label=item.get("label") or df.label;row.options=df.options;row.req=item.get("required",False) or df.reqd;row.read_only=item.get("read_only",False) or df.read_only
  if df.fieldtype=="Link" and row.meta.has_field("allow_read_on_all_link_options"):row.allow_read_on_all_link_options=1

def provision_procurement_web_forms():
 if not frappe.db.exists("DocType","Web Form"):return
 for d in WEB_FORMS:
  name=frappe.db.get_value("Web Form",{"route":d["route"]},"name");doc=frappe.get_doc("Web Form",name) if name else frappe.new_doc("Web Form")
  _apply_settings(doc,d);_rebuild_fields(doc,d)
  if doc.meta.has_field("client_script"):doc.client_script=""
  doc.save(ignore_permissions=True) if name else doc.insert(ignore_permissions=True)
 frappe.clear_cache(doctype="Web Form")
