import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

CUSTOM_FIELDS={"Company":[
 {"fieldname":"custom_allocation_rollback_section","label":"Allocation Rollback Policy","fieldtype":"Section Break","insert_after":"custom_allow_post_closeout_adjustment","collapsible":1,"is_system_generated":1,"module":"QOrg"},
 {"fieldname":"custom_posted_allocation_rollback_policy","label":"Posted Allocation Rollback Policy","fieldtype":"Select","options":"Reversal Entry Only\nControlled Cancellation\nReversal or Controlled Cancellation\nAdministrator Controlled","default":"Reversal Entry Only","insert_after":"custom_allocation_rollback_section","is_system_generated":1,"module":"QOrg","description":"Controls whether posted allocation runs must be reversed or may be cancelled with their original Journal Entry after dependency checks."},
 {"fieldname":"custom_original_cancellation_within_days","label":"Allow Original Cancellation Within Days","fieldtype":"Int","default":"7","non_negative":1,"insert_after":"custom_posted_allocation_rollback_policy","depends_on":"eval:doc.custom_posted_allocation_rollback_policy!=\"Reversal Entry Only\"","is_system_generated":1,"module":"QOrg"},
 {"fieldname":"custom_require_allocation_cancellation_reason","label":"Require Allocation Cancellation Reason","fieldtype":"Check","default":"1","insert_after":"custom_original_cancellation_within_days","is_system_generated":1,"module":"QOrg"},
],"Shared Cost Allocation Run":[{"fieldname":"workflow_state","label":"Workflow State","fieldtype":"Link","options":"Workflow State","insert_after":"run_status","read_only":1,"allow_on_submit":1,"is_system_generated":1,"module":"QOrg"},
 {"fieldname":"custom_rollback_method","label":"Rollback Method","fieldtype":"Select","options":"Controlled Cancellation\nReversal Entry","insert_after":"reversal_journal_entry","read_only":1,"allow_on_submit":1,"is_system_generated":1,"module":"QOrg"},
 {"fieldname":"custom_rollback_reason","label":"Rollback Reason","fieldtype":"Small Text","insert_after":"custom_rollback_method","read_only":1,"allow_on_submit":1,"is_system_generated":1,"module":"QOrg"},
 {"fieldname":"custom_rollback_by","label":"Rollback By","fieldtype":"Link","options":"User","insert_after":"custom_rollback_reason","read_only":1,"allow_on_submit":1,"is_system_generated":1,"module":"QOrg"},
 {"fieldname":"custom_rollback_on","label":"Rollback On","fieldtype":"Datetime","insert_after":"custom_rollback_by","read_only":1,"allow_on_submit":1,"is_system_generated":1,"module":"QOrg"}],"Journal Entry":[
 {"fieldname":"custom_qorg_source_section","label":"QOrg Source","fieldtype":"Section Break","insert_after":"user_remark","read_only":1,"is_system_generated":1,"module":"QOrg"},
 {"fieldname":"custom_qorg_source_doctype","label":"Source Document Type","fieldtype":"Link","options":"DocType","insert_after":"custom_qorg_source_section","read_only":1,"is_system_generated":1,"module":"QOrg"},
 {"fieldname":"custom_qorg_source_name","label":"Source Document","fieldtype":"Dynamic Link","options":"custom_qorg_source_doctype","insert_after":"custom_qorg_source_doctype","read_only":1,"is_system_generated":1,"module":"QOrg"},
 {"fieldname":"custom_qorg_source_hash","label":"Source Hash","fieldtype":"Data","insert_after":"custom_qorg_source_name","hidden":1,"read_only":1,"is_system_generated":1,"module":"QOrg"},
]}

def provision_service_allowance():
    create_custom_fields(CUSTOM_FIELDS,update=True)
    defaults=[
      {"type_name":"Site Rent","calculation_method":"Quantity x Rate","item_requirement":"Optional","procurement_treatment":"Framework Agreement Required","require_external_person":1,"require_site":1,"require_agreement":1,"require_identity_verification":1,"require_supporting_document":1,"require_project":1,"allow_shared_pool":1,"allow_split_distribution":1},
      {"type_name":"Daily Worker Wages","calculation_method":"Days x Daily Rate","item_requirement":"Optional","procurement_treatment":"Simplified Procurement","require_external_person":1,"require_attendance":1,"require_identity_verification":1,"require_supporting_document":1,"require_project":1,"allow_shared_pool":0,"allow_split_distribution":1},
      {"type_name":"Volunteer Allowance","calculation_method":"Fixed Amount","item_requirement":"Optional","procurement_treatment":"Not Applicable","require_external_person":1,"require_identity_verification":1,"require_supporting_document":1,"require_project":1,"allow_shared_pool":0,"allow_split_distribution":1},
    ]
    for values in defaults:
      if not frappe.db.exists("Service and Allowance Type",values["type_name"]):
        doc=frappe.new_doc("Service and Allowance Type");doc.update(values);doc.insert(ignore_permissions=True)
