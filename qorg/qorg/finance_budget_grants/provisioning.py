from __future__ import annotations
import frappe
from qorg.qorg.enterprise_foundation.idempotent_provisioning import create_custom_fields_if_changed
VERSION = "1.5.6"
PROJECT_SETTINGS_FIELDS=[
 {"fieldname":"custom_finance_grants_section","label":"Finance, Budgets and Grants","fieldtype":"Section Break","insert_after":"custom_project_cycle_defaults_initialized"},
 {"fieldname":"custom_default_budget_flexibility_percent","label":"Default Budget Flexibility (%)","fieldtype":"Percent","default":"10","insert_after":"custom_finance_grants_section"},
 {"fieldname":"custom_block_budget_overrun","label":"Block Budget Overrun","fieldtype":"Check","default":"1","insert_after":"custom_default_budget_flexibility_percent"},
 {"fieldname":"custom_finance_grants_column","fieldtype":"Column Break","insert_after":"custom_block_budget_overrun"},
 {"fieldname":"custom_require_funding_agreement","label":"Require Funding Agreement","fieldtype":"Check","default":"1","insert_after":"custom_finance_grants_column"},
 {"fieldname":"custom_enforce_eligibility_period","label":"Enforce Eligibility Period","fieldtype":"Check","default":"1","insert_after":"custom_require_funding_agreement"},
 {"fieldname":"custom_finance_grants_audit_section","label":"Finance Cycle Audit","fieldtype":"Section Break","insert_after":"custom_enforce_eligibility_period"},
 {"fieldname":"custom_finance_grants_version","label":"Finance Configuration Version","fieldtype":"Data","read_only":1,"insert_after":"custom_finance_grants_audit_section"},
 {"fieldname":"custom_finance_grants_last_audit","label":"Last Finance Audit","fieldtype":"Datetime","read_only":1,"insert_after":"custom_finance_grants_version"},
]
CUSTOM_FIELDS={
 "Projects Settings":PROJECT_SETTINGS_FIELDS,
 "Budget Line":[
  {"fieldname":"custom_finance_section","label":"Funding and Budget Control","fieldtype":"Section Break","insert_after":"latest_change_request"},
  {"fieldname":"project_funding_source_row","label":"Project Funding Source Row","fieldtype":"Data","read_only":1,"hidden":1,"insert_after":"custom_finance_section"},
  {"fieldname":"source_donor","label":"Source Donor","fieldtype":"Link","options":"Donor","read_only":1,"insert_after":"project_funding_source_row"},
  {"fieldname":"funding_agreement","label":"Funding Agreement","fieldtype":"Link","options":"Funding Agreement","insert_after":"source_donor"},
  {"fieldname":"cost_category","label":"Cost Category","fieldtype":"Select","options":"Direct Cost\nIndirect Cost\nShared Cost\nCapital Cost","default":"Direct Cost","insert_after":"funding_agreement"},
  {"fieldname":"custom_finance_column","fieldtype":"Column Break","insert_after":"cost_category"},
  {"fieldname":"allow_budget_transfer","label":"Allow Budget Transfer","fieldtype":"Check","default":"1","insert_after":"custom_finance_column"},
  {"fieldname":"flexibility_percent","label":"Flexibility (%)","fieldtype":"Percent","default":"10","insert_after":"allow_budget_transfer"},
  {"fieldname":"eligibility_start_date","label":"Eligibility Start Date","fieldtype":"Date","insert_after":"flexibility_percent"},
  {"fieldname":"eligibility_end_date","label":"Eligibility End Date","fieldtype":"Date","insert_after":"eligibility_start_date"},
  {"fieldname":"finance_values_overridden","label":"Finance Values Overridden","fieldtype":"Check","default":"0","read_only":1,"insert_after":"eligibility_end_date"},
  {"fieldname":"current_approved_amount","label":"Current Approved Amount","fieldtype":"Currency","options":"currency","read_only":1,"allow_on_submit":1,"insert_after":"original_approved_amount"},
 ],
 "Project Change Request":[
  {"fieldname":"custom_budget_change_section","label":"Budget Change Control","fieldtype":"Section Break","insert_after":"change_type"},
  {"fieldname":"funding_agreement","label":"Funding Agreement","fieldtype":"Link","options":"Funding Agreement","insert_after":"custom_budget_change_section"},
  {"fieldname":"budget_transfer_required","label":"Budget Transfer Required","fieldtype":"Check","default":"0","insert_after":"funding_agreement"},
  {"fieldname":"budget_transfer_amount","label":"Budget Transfer Amount","fieldtype":"Currency","read_only":1,"depends_on":"eval:doc.budget_transfer_required","insert_after":"budget_transfer_required"},
  {"fieldname":"donor_approval_required","label":"Donor Approval Required","fieldtype":"Check","default":"0","read_only":1,"depends_on":"eval:doc.budget_transfer_required","insert_after":"budget_transfer_amount"},
  {"fieldname":"donor_approval_reference","label":"Donor Approval Reference","fieldtype":"Data","depends_on":"eval:doc.donor_approval_required","mandatory_depends_on":"eval:doc.donor_approval_required","insert_after":"donor_approval_required"},
  {"fieldname":"budget_transfer_rows","label":"Budget Transfer Rows","fieldtype":"Table","options":"Budget Transfer Item","depends_on":"eval:doc.budget_transfer_required","mandatory_depends_on":"eval:doc.budget_transfer_required","insert_after":"donor_approval_reference"},
  {"fieldname":"budget_transfer_applied_on","label":"Budget Transfer Applied On","fieldtype":"Datetime","read_only":1,"allow_on_submit":1,"insert_after":"budget_transfer_rows"},
  {"fieldname":"budget_transfer_applied_by","label":"Budget Transfer Applied By","fieldtype":"Link","options":"User","read_only":1,"allow_on_submit":1,"insert_after":"budget_transfer_applied_on"},
  {"fieldname":"budget_transfer_audit","label":"Budget Transfer Audit","fieldtype":"Link","options":"Budget Transfer Audit","read_only":1,"allow_on_submit":1,"insert_after":"budget_transfer_applied_by"},
 ],
 "Project Closure":[
  {"fieldname":"custom_financial_closeout_section","label":"Financial and Grant Closeout","fieldtype":"Section Break","insert_after":"closure_date"},
  {"fieldname":"open_commitments_amount","label":"Open Commitments","fieldtype":"Currency","read_only":1,"insert_after":"custom_financial_closeout_section"},
  {"fieldname":"unsettled_advances_amount","label":"Unsettled Advances","fieldtype":"Currency","read_only":1,"insert_after":"open_commitments_amount"},
  {"fieldname":"financial_closeout_completed","label":"Financial Closeout Completed","fieldtype":"Check","default":"0","insert_after":"unsettled_advances_amount"},
  {"fieldname":"grant_closeout_completed","label":"Grant Closeout Completed","fieldtype":"Check","default":"0","insert_after":"financial_closeout_completed"},
 ]
}
def provision_finance_budget_grants():
 for dt,fields in CUSTOM_FIELDS.items():
  if frappe.db.exists("DocType",dt): create_custom_fields_if_changed({dt:fields},update=True)
 if frappe.db.exists("DocType","Projects Settings"):
  doc=frappe.get_single("Projects Settings")
  if hasattr(doc,"custom_finance_grants_version"):
   doc.db_set("custom_finance_grants_version",VERSION,update_modified=False)
 from .workflows import provision_workflow
 from .notifications import provision_notifications
 provision_workflow()
 provision_notifications()
 frappe.clear_cache()
 return {"version":VERSION,"doctypes":list(CUSTOM_FIELDS)}
