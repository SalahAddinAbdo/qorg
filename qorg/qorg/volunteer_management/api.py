import frappe
from frappe import _
from frappe.utils import cint, now_datetime
from . import services

def _manager():
    if frappe.session.user!="Administrator" and not ({"Volunteer Manager","Volunteer Coordinator"}&set(frappe.get_roles())):frappe.throw(_("Volunteer management role is required."),frappe.PermissionError)
@frappe.whitelist(methods=["POST"])
def create_retry_assessment(assessment,retry_reason=None):
    _manager();source=frappe.get_doc("Participation Assessment",assessment);source.check_permission("read")
    if source.status!="Completed" or source.result!="Failed" or not source.allow_retry:frappe.throw(_("This assessment is not eligible for retry."))
    if cint(source.attempt_number)>=cint(source.maximum_attempts):frappe.throw(_("Maximum attempts have been reached."))
    existing=frappe.db.get_value("Participation Assessment",{"previous_assessment":source.name,"status":["!=","Cancelled"]},"name")
    if existing:return existing
    doc=frappe.new_doc("Participation Assessment")
    for field in ("application","opportunity","stage_sequence","stage_name","assessment_method","allow_retry","maximum_attempts","retry_requires_approval"):
        doc.set(field,source.get(field))
    doc.attempt_number=cint(source.attempt_number)+1;doc.previous_assessment=source.name;doc.retry_reason=retry_reason
    if source.retry_requires_approval:doc.retry_approved_by=frappe.session.user;doc.retry_approved_on=now_datetime()
    doc.insert();return doc.name
@frappe.whitelist(methods=["POST"])
def create_engagement(application):
    _manager();app=frappe.get_doc("Participation Application",application);app.check_permission("read")
    if app.final_decision!="Selected":frappe.throw(_("Only selected applications can create an engagement."))
    existing=frappe.db.get_value("Participation Engagement",{"application":app.name,"docstatus":["<",2]},"name")
    if existing:return existing
    opp=frappe.get_doc("External Opportunity",app.opportunity);doc=frappe.new_doc("Participation Engagement")
    doc.update({"application":app.name,"external_person":app.external_person,"opportunity":app.opportunity,"participation_type":app.participation_type,"project":app.project,"branch":app.branch,"role_title":opp.get("title") or opp.name,"supervisor":opp.get("qorg_supervisor"),"expected_hours":opp.get("qorg_expected_hours"),"status":"Pending Onboarding","company":opp.get("company")})
    doc.insert();return doc.name

@frappe.whitelist(methods=["POST"])
def initialize_assessments(application):
    _manager();app=frappe.get_doc("Participation Application",application);app.check_permission("read")
    opportunity=frappe.get_doc("External Opportunity",app.opportunity);created=[]
    for stage in opportunity.get("qorg_assessment_plan") or []:
        existing=frappe.db.get_value("Participation Assessment",{"application":app.name,"stage_sequence":stage.sequence,"status":["!=","Cancelled"]},"name")
        if existing:continue
        doc=frappe.new_doc("Participation Assessment");doc.application=app.name;doc.stage_sequence=stage.sequence;doc.insert();created.append(doc.name)
    if created:frappe.db.set_value("Participation Application",app.name,"status","Under Assessment",update_modified=False)
    return created

@frappe.whitelist()
def preview_notification(notification_type,template,reference_doctype,reference_name,primary_recipient=None,cc_json=None,users_json=None):
    from .notifications import preview_participation_message
    return preview_participation_message(notification_type,template,reference_doctype,reference_name,primary_recipient,cc_json,users_json)

@frappe.whitelist(methods=["POST"])
def send_notification(notification_type,template,reference_doctype,reference_name,primary_recipient=None,cc_json=None,users_json=None,force=0):
    _manager();from .notifications import send_participation_message
    return send_participation_message(notification_type,template,reference_doctype,reference_name,primary_recipient,cc_json,users_json,force)

@frappe.whitelist(methods=["POST"])
def transition_engagement(name,action,remarks=None):
    _manager();doc=frappe.get_doc("Participation Engagement",name);doc.check_permission("write")
    mapping={"Activate":"Active","Suspend":"Suspended","Complete":"Completed","Terminate":"Terminated","Withdraw":"Withdrawn"}
    if action not in mapping:frappe.throw(_("Unsupported action."))
    doc.status=mapping[action]
    if action in {"Terminate","Withdraw"}:doc.exit_date=frappe.utils.today();doc.exit_remarks=remarks
    doc.save();return doc.name

@frappe.whitelist(methods=["POST"])
def create_evaluation(engagement,evaluation_type):
    _manager();eng=frappe.get_doc("Participation Engagement",engagement);eng.check_permission("read")
    existing=frappe.db.get_value("Participation Evaluation",{"engagement":eng.name,"evaluation_type":evaluation_type,"status":["!=","Cancelled"]},"name")
    if existing:return existing
    doc=frappe.new_doc("Participation Evaluation");doc.engagement=eng.name;doc.external_person=eng.external_person;doc.evaluation_type=evaluation_type;doc.evaluator=frappe.session.user;doc.insert();return doc.name

@frappe.whitelist(methods=["POST"])
def issue_certificate(engagement):
    _manager();eng=frappe.get_doc("Participation Engagement",engagement);eng.check_permission("read")
    existing=frappe.db.get_value("Participation Certificate",{"engagement":eng.name,"status":["!=","Revoked"]},"name")
    if existing:return existing
    doc=frappe.new_doc("Participation Certificate");doc.engagement=eng.name;doc.external_person=eng.external_person;doc.participation_type=eng.participation_type;doc.status="Issued";doc.insert();frappe.db.set_value("Participation Engagement",eng.name,"certificate",doc.name,update_modified=False);return doc.name
