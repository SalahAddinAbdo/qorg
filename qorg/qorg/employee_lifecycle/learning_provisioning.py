import frappe
from qorg.qorg.enterprise_foundation.idempotent_provisioning import create_custom_fields_if_changed

FIELDS = {
 "Training Program": [
  {"fieldname":"qorg_training_need_request","label":"Source Training Need Request","fieldtype":"Link","options":"Training Need Request","insert_after":"company","read_only":1,"in_standard_filter":1},
 ],
 "Training Event": [
  {"fieldname":"qorg_training_need_request","label":"Source Training Need Request","fieldtype":"Link","options":"Training Need Request","insert_after":"company","read_only":1,"in_standard_filter":1},
  {"fieldname":"qorg_development_context_section","label":"Development and Funding Context","fieldtype":"Section Break","insert_after":"introduction","collapsible":1},
  {"fieldname":"qorg_project","label":"Project","fieldtype":"Link","options":"Project","insert_after":"qorg_development_context_section"},
  {"fieldname":"qorg_cost_center","label":"Cost Center","fieldtype":"Link","options":"Cost Center","insert_after":"qorg_project"},
  {"fieldname":"qorg_context_column","fieldtype":"Column Break","insert_after":"qorg_cost_center"},
  {"fieldname":"qorg_funding_agreement","label":"Funding Agreement","fieldtype":"Link","options":"Funding Agreement","insert_after":"qorg_context_column"},
  {"fieldname":"qorg_budget_line","label":"Budget Line","fieldtype":"Link","options":"Budget Line","insert_after":"qorg_funding_agreement"},
 ],
}

def provision_learning_planning():
    definitions={dt:rows for dt,rows in FIELDS.items() if frappe.db.exists("DocType",dt)}
    return create_custom_fields_if_changed(definitions,update=True) if definitions else {"changed":[],"unchanged":[]}
