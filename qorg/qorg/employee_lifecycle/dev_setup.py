import frappe
from qorg.qorg.enterprise_foundation.idempotent_provisioning import create_custom_fields_if_changed
FIELDS={
 "Designation Skill":[
  {"fieldname":"qorg_required_level","label":"Required Level","fieldtype":"Rating","options":"5","insert_after":"skill","in_list_view":1},
  {"fieldname":"qorg_mandatory","label":"Mandatory","fieldtype":"Check","default":"0","insert_after":"qorg_required_level","in_list_view":1},
 ],
 "Skill Assessment":[
  {"fieldname":"qorg_required_level","label":"Required Level","fieldtype":"Rating","options":"5","insert_after":"rating","read_only":1,"in_list_view":1},
  {"fieldname":"qorg_assessment_method","label":"Assessment Method","fieldtype":"Select","options":"Manager Review\nPractical Test\nCertification\nPeer Review\nSelf Assessment\nTraining Result","insert_after":"qorg_required_level","in_list_view":1},
  {"fieldname":"qorg_evidence","label":"Evidence","fieldtype":"Link","options":"Employee Document Record","insert_after":"qorg_assessment_method"},
  {"fieldname":"qorg_valid_until","label":"Valid Until","fieldtype":"Date","insert_after":"qorg_evidence","in_list_view":1},
 ],
 "Employee Skill":[
  {"fieldname":"qorg_source_doctype","label":"Source Type","fieldtype":"Link","options":"DocType","insert_after":"evaluation_date"},
  {"fieldname":"qorg_source_document","label":"Source Document","fieldtype":"Dynamic Link","options":"qorg_source_doctype","insert_after":"qorg_source_doctype"},
  {"fieldname":"qorg_evidence","label":"Evidence","fieldtype":"Link","options":"Employee Document Record","insert_after":"qorg_source_document"},
  {"fieldname":"qorg_valid_until","label":"Valid Until","fieldtype":"Date","insert_after":"qorg_evidence","in_list_view":1},
 ],
 "Appraisal":[
  {"fieldname":"qorg_recommend_section","label":"Recommendations and Actions","fieldtype":"Section Break","insert_after":"reflections","collapsible":1},
  {"fieldname":"qorg_promotion_recommended","label":"Promotion Recommended","fieldtype":"Check","default":"0","insert_after":"qorg_recommend_section"},
  {"fieldname":"qorg_transfer_recommended","label":"Transfer Recommended","fieldtype":"Check","default":"0","insert_after":"qorg_promotion_recommended"},
  {"fieldname":"qorg_salary_recommended","label":"Salary Change Recommended","fieldtype":"Check","default":"0","insert_after":"qorg_transfer_recommended"},
  {"fieldname":"qorg_recommend_column","fieldtype":"Column Break","insert_after":"qorg_salary_recommended"},
  {"fieldname":"qorg_contract_recommended","label":"Contract Renewal Recommended","fieldtype":"Check","default":"0","insert_after":"qorg_recommend_column"},
  {"fieldname":"qorg_funding_recommended","label":"Funding Change Recommended","fieldtype":"Check","default":"0","insert_after":"qorg_contract_recommended"},
  {"fieldname":"qorg_training_recommended","label":"Training Recommended","fieldtype":"Check","default":"0","insert_after":"qorg_funding_recommended"},
  {"fieldname":"qorg_recommend_notes","label":"Recommendation Notes","fieldtype":"Small Text","insert_after":"qorg_training_recommended"},
  {"fieldname":"qorg_action_section","label":"Execution References","fieldtype":"Section Break","insert_after":"qorg_recommend_notes","collapsible":1},
  {"fieldname":"qorg_promotion","label":"Employee Promotion","fieldtype":"Link","options":"Employee Promotion","read_only":1,"insert_after":"qorg_action_section"},
  {"fieldname":"qorg_transfer","label":"Employee Transfer","fieldtype":"Link","options":"Employee Transfer","read_only":1,"insert_after":"qorg_promotion"},
  {"fieldname":"qorg_salary_assignment","label":"Salary Structure Assignment","fieldtype":"Link","options":"Salary Structure Assignment","read_only":1,"insert_after":"qorg_transfer"},
  {"fieldname":"qorg_action_column","fieldtype":"Column Break","insert_after":"qorg_salary_assignment"},
  {"fieldname":"qorg_contract_amendment","label":"Contract Amendment","fieldtype":"Link","options":"Contract Amendment","read_only":1,"insert_after":"qorg_action_column"},
  {"fieldname":"qorg_funding_plan","label":"Workforce Funding Plan","fieldtype":"Link","options":"Workforce Funding Plan","read_only":1,"insert_after":"qorg_contract_amendment"},
  {"fieldname":"qorg_development_action","label":"Development Action","fieldtype":"Link","options":"Development Action","read_only":1,"insert_after":"qorg_funding_plan"},
 ],
}
def setup_development():
 definitions={dt:rows for dt,rows in FIELDS.items() if frappe.db.exists("DocType",dt)}
 return create_custom_fields_if_changed(definitions,update=True) if definitions else {"changed":[],"unchanged":[]}
