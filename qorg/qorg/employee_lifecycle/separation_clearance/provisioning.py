from __future__ import annotations
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
STATUS="Not Checked\nPending\nClear\nException Approved"
def _anchor(meta):
 for x in ("activities","boarding_status","employee"):
  if meta.has_field(x):return x
 return meta.fields[-1].fieldname if meta.fields else None
def _rows(dt):
 m=frappe.get_meta(dt,cached=False);a=_anchor(m)
 return [
 {"fieldname":"custom_qorg_clearance_tab","label":"Clearance and Closeout","fieldtype":"Tab Break","insert_after":a},
 {"fieldname":"custom_qorg_employee_context","label":"Employee and Handover","fieldtype":"Section Break","insert_after":"custom_qorg_clearance_tab"},
 {"fieldname":"custom_employee_name","label":"Employee Name","fieldtype":"Data","fetch_from":"employee.employee_name","read_only":1,"insert_after":"custom_qorg_employee_context"},
 {"fieldname":"custom_company","label":"Company","fieldtype":"Link","options":"Company","fetch_from":"employee.company","read_only":1,"insert_after":"custom_employee_name"},
 {"fieldname":"custom_branch","label":"Branch","fieldtype":"Link","options":"Branch","fetch_from":"employee.branch","read_only":1,"insert_after":"custom_company"},
 {"fieldname":"custom_context_col_2","fieldtype":"Column Break","insert_after":"custom_branch"},
 {"fieldname":"custom_department","label":"Department","fieldtype":"Link","options":"Department","fetch_from":"employee.department","read_only":1,"insert_after":"custom_context_col_2"},
 {"fieldname":"custom_designation","label":"Designation","fieldtype":"Link","options":"Designation","fetch_from":"employee.designation","read_only":1,"insert_after":"custom_department"},
 {"fieldname":"custom_reports_to","label":"Reports To","fieldtype":"Link","options":"Employee","fetch_from":"employee.reports_to","read_only":1,"insert_after":"custom_designation"},
 {"fieldname":"custom_contract","label":"Contract","fieldtype":"Link","options":"Contract","insert_after":"custom_reports_to"},
 {"fieldname":"custom_last_working_date","label":"Last Working Date","fieldtype":"Date","read_only":1,"insert_after":"custom_contract"},
 {"fieldname":"custom_handover_to_employee","label":"Handover To Employee","fieldtype":"Link","options":"Employee","insert_after":"custom_last_working_date"},
 {"fieldname":"custom_context_col_3","fieldtype":"Column Break","insert_after":"custom_handover_to_employee"},
 {"fieldname":"custom_handover_to_user","label":"Handover To User","fieldtype":"Link","options":"User","fetch_from":"custom_handover_to_employee.user_id","read_only":1,"insert_after":"custom_context_col_3"},
 {"fieldname":"custom_user_id","label":"Departing User","fieldtype":"Link","options":"User","fetch_from":"employee.user_id","read_only":1,"insert_after":"custom_handover_to_user"},
 {"fieldname":"custom_exit_interview_required","label":"Exit Interview Required","fieldtype":"Check","default":"1","insert_after":"custom_user_id"},
 {"fieldname":"custom_final_settlement_required","label":"Final Settlement Required","fieldtype":"Check","default":"1","insert_after":"custom_exit_interview_required"},
 {"fieldname":"custom_qorg_summary","label":"Clearance Summary","fieldtype":"Section Break","insert_after":"custom_final_settlement_required"},
 {"fieldname":"custom_overall_clearance_status","label":"Overall Clearance Status","fieldtype":"Select","options":"Not Started\nIn Progress\nBlocked\nReady for Approval\nCompleted\nReopened","default":"Not Started","read_only":1,"in_standard_filter":1,"insert_after":"custom_qorg_summary"},
 {"fieldname":"custom_completion_percentage","label":"Completion Percentage","fieldtype":"Percent","read_only":1,"insert_after":"custom_overall_clearance_status"},
 {"fieldname":"custom_required_items","label":"Required Items","fieldtype":"Int","read_only":1,"insert_after":"custom_completion_percentage"},
 {"fieldname":"custom_summary_col_2","fieldtype":"Column Break","insert_after":"custom_required_items"},
 {"fieldname":"custom_completed_items","label":"Completed Items","fieldtype":"Int","read_only":1,"insert_after":"custom_summary_col_2"},
 {"fieldname":"custom_blocked_items","label":"Blocked Items","fieldtype":"Int","read_only":1,"insert_after":"custom_completed_items"},
 {"fieldname":"custom_total_outstanding_amount","label":"Outstanding Amount","fieldtype":"Currency","read_only":1,"insert_after":"custom_blocked_items"},
 {"fieldname":"custom_summary_col_3","fieldtype":"Column Break","insert_after":"custom_total_outstanding_amount"},
 {"fieldname":"custom_clearance_completed_on","label":"Clearance Completed On","fieldtype":"Datetime","read_only":1,"depends_on":"eval:doc.custom_overall_clearance_status=='Completed'","insert_after":"custom_summary_col_3"},
 {"fieldname":"custom_clearance_completed_by","label":"Clearance Completed By","fieldtype":"Link","options":"User","read_only":1,"depends_on":"eval:doc.custom_overall_clearance_status=='Completed'","insert_after":"custom_clearance_completed_on"},
 {"fieldname":"custom_qorg_domains","label":"Domain Status","fieldtype":"Section Break","insert_after":"custom_clearance_completed_by"},
 {"fieldname":"custom_financial_clearance_status","label":"Financial Clearance","fieldtype":"Select","options":STATUS,"default":"Not Checked","read_only":1,"insert_after":"custom_qorg_domains"},
 {"fieldname":"custom_payroll_clearance_status","label":"Payroll Clearance","fieldtype":"Select","options":STATUS,"default":"Not Checked","read_only":1,"insert_after":"custom_financial_clearance_status"},
 {"fieldname":"custom_asset_clearance_status","label":"Asset Clearance","fieldtype":"Select","options":STATUS,"default":"Not Checked","read_only":1,"insert_after":"custom_payroll_clearance_status"},
 {"fieldname":"custom_domains_col_2","fieldtype":"Column Break","insert_after":"custom_asset_clearance_status"},
 {"fieldname":"custom_stock_clearance_status","label":"Stock Clearance","fieldtype":"Select","options":STATUS,"default":"Not Checked","read_only":1,"insert_after":"custom_domains_col_2"},
 {"fieldname":"custom_contract_clearance_status","label":"Contract Clearance","fieldtype":"Select","options":STATUS,"default":"Not Checked","read_only":1,"insert_after":"custom_stock_clearance_status"},
 {"fieldname":"custom_document_clearance_status","label":"Document Clearance","fieldtype":"Select","options":STATUS,"default":"Not Checked","read_only":1,"insert_after":"custom_contract_clearance_status"},
 {"fieldname":"custom_domains_col_3","fieldtype":"Column Break","insert_after":"custom_document_clearance_status"},
 {"fieldname":"custom_system_access_status","label":"System Access","fieldtype":"Select","options":"Not Checked\nPending Closure\nClosed\nException Approved","default":"Not Checked","read_only":1,"insert_after":"custom_domains_col_3"},
 {"fieldname":"custom_exit_interview","label":"Exit Interview","fieldtype":"Link","options":"Exit Interview","depends_on":"eval:doc.custom_exit_interview_required","insert_after":"custom_system_access_status"},
 {"fieldname":"custom_full_and_final_statement","label":"Full and Final Statement","fieldtype":"Link","options":"Full and Final Statement","depends_on":"eval:doc.custom_final_settlement_required","insert_after":"custom_exit_interview"},
 {"fieldname":"custom_qorg_items","label":"Clearance Items","fieldtype":"Section Break","insert_after":"custom_full_and_final_statement"},
 {"fieldname":"custom_clearance_items","label":"Clearance Items","fieldtype":"Table","options":"Employee Clearance Item","insert_after":"custom_qorg_items"},
 {"fieldname":"custom_qorg_controls","label":"Closeout Controls","fieldtype":"Section Break","insert_after":"custom_clearance_items"},
 {"fieldname":"custom_handover_completed","label":"Handover Completed","fieldtype":"Check","read_only":1,"insert_after":"custom_qorg_controls"},
 {"fieldname":"custom_responsibilities_transferred","label":"Responsibilities Transferred","fieldtype":"Check","read_only":1,"insert_after":"custom_handover_completed"},
 {"fieldname":"custom_access_closed_on","label":"Access Closed On","fieldtype":"Datetime","read_only":1,"depends_on":"eval:doc.custom_system_access_status=='Closed'","insert_after":"custom_responsibilities_transferred"},
 {"fieldname":"custom_controls_col_2","fieldtype":"Column Break","insert_after":"custom_access_closed_on"},
 {"fieldname":"custom_reopened","label":"Reopened","fieldtype":"Check","read_only":1,"insert_after":"custom_controls_col_2"},
 {"fieldname":"custom_reopen_reason","label":"Reopen Reason","fieldtype":"Small Text","depends_on":"eval:doc.custom_reopened","mandatory_depends_on":"eval:doc.custom_reopened","insert_after":"custom_reopened"},
 {"fieldname":"custom_qorg_audit","label":"Clearance Audit","fieldtype":"Section Break","collapsible":1,"insert_after":"custom_reopen_reason"},
 {"fieldname":"custom_clearance_snapshot","label":"Clearance Snapshot","fieldtype":"Code","options":"JSON","read_only":1,"insert_after":"custom_qorg_audit"},]
def _notification(dt):
 name=f"{dt} Clearance Status Changed - Bilingual"; vals={"document_type":dt,"event":"Value Change","value_changed":"custom_overall_clearance_status","subject":"Clearance status changed | تغيرت حالة إخلاء الطرف","message":"<p>Clearance status: <b>{{ doc.custom_overall_clearance_status }}</b></p><p dir='rtl'>حالة إخلاء الطرف: <b>{{ doc.custom_overall_clearance_status }}</b></p>","enabled":1,"channel":"Email"}
 doc=frappe.get_doc("Notification",name) if frappe.db.exists("Notification",name) else frappe.new_doc("Notification");doc.name=name;doc.update(vals);doc.set("recipients",[]);doc.append("recipients",{"receiver_by_role":"HR Manager"});doc.save(ignore_permissions=True)
def provision_employee_separation_clearance():
 mapping={dt:_rows(dt) for dt in ("Employee Separation","Employee Offboarding") if frappe.db.exists("DocType",dt)}
 if mapping:create_custom_fields(mapping,update=True)
 for dt in mapping:_notification(dt)
 frappe.clear_cache()
