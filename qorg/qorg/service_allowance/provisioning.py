import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

CUSTOM_FIELDS={"Shared Cost Allocation Run":[{"fieldname":"workflow_state","label":"Workflow State","fieldtype":"Link","options":"Workflow State","insert_after":"run_status","read_only":1,"allow_on_submit":1,"is_system_generated":1,"module":"QOrg"}],"Journal Entry":[
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
