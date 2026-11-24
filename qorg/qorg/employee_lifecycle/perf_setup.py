import frappe
from qorg.qorg.enterprise_foundation.idempotent_provisioning import create_custom_fields_if_changed
FIELDS={
 "Appraisal Cycle":[
  {"fieldname":"qorg_policy_section","label":"Evaluation Policy","fieldtype":"Section Break","insert_after":"description","collapsible":1},
  {"fieldname":"qorg_evaluation_type","label":"Evaluation Type","fieldtype":"Link","options":"Evaluation Type","insert_after":"qorg_policy_section","in_standard_filter":1},
  {"fieldname":"qorg_policy_snapshot","label":"Policy Snapshot","fieldtype":"Long Text","read_only":1,"hidden":1,"insert_after":"qorg_evaluation_type"},
  {"fieldname":"qorg_assignment_status","label":"Assignment Generation Status","fieldtype":"Select","options":"Not Started\nPartial\nComplete","default":"Not Started","read_only":1,"insert_after":"qorg_policy_snapshot"},
 ],
 "Appraisal":[
  {"fieldname":"qorg_evaluation_type","label":"Evaluation Type","fieldtype":"Link","options":"Evaluation Type","insert_after":"appraisal_cycle","read_only":1,"in_standard_filter":1},
  {"fieldname":"qorg_assignment_total","label":"Assignments","fieldtype":"Int","read_only":1,"insert_after":"qorg_evaluation_type"},
  {"fieldname":"qorg_assignment_submitted","label":"Submitted Feedback","fieldtype":"Int","read_only":1,"insert_after":"qorg_assignment_total"},
  {"fieldname":"qorg_assignment_pending","label":"Pending Feedback","fieldtype":"Int","read_only":1,"insert_after":"qorg_assignment_submitted"},
 ],
 "Employee Performance Feedback":[
  {"fieldname":"qorg_assignment","label":"Evaluation Assignment","fieldtype":"Link","options":"Evaluation Assignment","insert_after":"appraisal","read_only":1,"in_standard_filter":1},
  {"fieldname":"qorg_evaluation_source","label":"Evaluation Source","fieldtype":"Data","insert_after":"qorg_assignment","read_only":1,"in_standard_filter":1},
  {"fieldname":"qorg_weight","label":"Weight (%)","fieldtype":"Percent","insert_after":"qorg_evaluation_source","read_only":1},
  {"fieldname":"qorg_anonymous","label":"Anonymous","fieldtype":"Check","insert_after":"qorg_weight","read_only":1},
  {"fieldname":"qorg_feedback_detail_section","label":"Comments and Evidence","fieldtype":"Section Break","insert_after":"qorg_anonymous"},
  {"fieldname":"qorg_evidence","label":"Evidence","fieldtype":"Link","options":"Employee Document Record","insert_after":"qorg_feedback_detail_section"},
  {"fieldname":"qorg_comments","label":"Evaluation Comments","fieldtype":"Text Editor","insert_after":"qorg_evidence"},
 ],
}
def setup_performance_policy():
 definitions={dt:rows for dt,rows in FIELDS.items() if frappe.db.exists("DocType",dt)}
 return create_custom_fields_if_changed(definitions,update=True) if definitions else {"changed":[],"unchanged":[]}

APPRAISAL_LIFECYCLE_FIELDS = [
  {"fieldname":"qorg_lifecycle_tab","label":"Evaluation Lifecycle","fieldtype":"Tab Break","insert_after":"reflections"},
  {"fieldname":"qorg_stage_section","label":"Evaluation Stage","fieldtype":"Section Break","insert_after":"qorg_lifecycle_tab"},
  {"fieldname":"qorg_stage","label":"Evaluation Stage","fieldtype":"Select","options":"Preparation\nGoal Setting\nGoal Tracking\nSelf-Appraisal Open\nFeedback Collection\nHR Review\nFinalized\nClosed\nReopened\nCancelled","default":"Preparation","read_only":1,"insert_after":"qorg_stage_section","in_standard_filter":1},
  {"fieldname":"qorg_stage_by","label":"Stage Updated By","fieldtype":"Link","options":"User","read_only":1,"insert_after":"qorg_stage"},
  {"fieldname":"qorg_stage_on","label":"Stage Updated On","fieldtype":"Datetime","read_only":1,"insert_after":"qorg_stage_by"},
  {"fieldname":"qorg_stage_column","fieldtype":"Column Break","insert_after":"qorg_stage_on"},
  {"fieldname":"qorg_finalized_by","label":"Finalized By","fieldtype":"Link","options":"User","read_only":1,"insert_after":"qorg_stage_column"},
  {"fieldname":"qorg_finalized_on","label":"Finalized On","fieldtype":"Datetime","read_only":1,"insert_after":"qorg_finalized_by"},
  {"fieldname":"qorg_reopened_by","label":"Reopened By","fieldtype":"Link","options":"User","read_only":1,"insert_after":"qorg_finalized_on"},
  {"fieldname":"qorg_reopened_on","label":"Reopened On","fieldtype":"Datetime","read_only":1,"insert_after":"qorg_reopened_by"},
  {"fieldname":"qorg_reopen_reason","label":"Reopen Reason","fieldtype":"Small Text","read_only":1,"insert_after":"qorg_reopened_on"},
  {"fieldname":"qorg_cancel_reason","label":"Cancel Reason","fieldtype":"Small Text","read_only":1,"insert_after":"qorg_reopen_reason"},
  {"fieldname":"qorg_result_section","label":"Calculated Result","fieldtype":"Section Break","insert_after":"qorg_cancel_reason"},
  {"fieldname":"qorg_completion","label":"Completion (%)","fieldtype":"Percent","read_only":1,"insert_after":"qorg_result_section"},
  {"fieldname":"qorg_final_score","label":"Final Score (%)","fieldtype":"Percent","read_only":1,"insert_after":"qorg_completion"},
  {"fieldname":"qorg_rating","label":"Rating","fieldtype":"Data","read_only":1,"insert_after":"qorg_final_score"},
  {"fieldname":"qorg_result_column","fieldtype":"Column Break","insert_after":"qorg_rating"},
  {"fieldname":"qorg_outcome","label":"Outcome","fieldtype":"Select","options":"\nIncomplete\nPassed\nDevelopment Plan\nFailed","read_only":1,"insert_after":"qorg_result_column"},
  {"fieldname":"qorg_provisional","label":"Provisional","fieldtype":"Check","read_only":1,"insert_after":"qorg_outcome"},
  {"fieldname":"qorg_calculated_by","label":"Calculated By","fieldtype":"Link","options":"User","read_only":1,"insert_after":"qorg_provisional"},
  {"fieldname":"qorg_calculated_on","label":"Calculated On","fieldtype":"Datetime","read_only":1,"insert_after":"qorg_calculated_by"},
  {"fieldname":"qorg_source_section","label":"Source Results","fieldtype":"Section Break","insert_after":"qorg_calculated_on"},
  {"fieldname":"qorg_source_results","label":"Source Results","fieldtype":"Table","options":"Evaluation Result","read_only":1,"insert_after":"qorg_source_section"},
  {"fieldname":"qorg_calc_section","label":"Calculation History","fieldtype":"Section Break","collapsible":1,"insert_after":"qorg_source_results"},
  {"fieldname":"qorg_calc_log","label":"Calculation History","fieldtype":"Table","options":"Calculation Log","read_only":1,"insert_after":"qorg_calc_section"},
  {"fieldname":"qorg_calc_snapshot","label":"Latest Calculation Snapshot","fieldtype":"Long Text","read_only":1,"hidden":1,"insert_after":"qorg_calc_log"},
]

_old_setup_performance_policy = setup_performance_policy
def setup_performance_policy():
    definitions={dt:list(rows) for dt,rows in FIELDS.items() if frappe.db.exists("DocType",dt)}
    if frappe.db.exists("DocType","Appraisal"):
        definitions.setdefault("Appraisal",[]).extend(APPRAISAL_LIFECYCLE_FIELDS)
    return create_custom_fields_if_changed(definitions,update=True) if definitions else {"changed":[],"unchanged":[]}
