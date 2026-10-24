import hashlib
import json
import frappe
from frappe import _
from frappe.utils import now_datetime
from .settings import get_settings

ALLOWED_REFERENCES={
    "Application Not Selected":{"Job Applicant"},"Reserve Candidate":{"Job Applicant"},
    "Interview Invitation":{"Interview"},"Interview Rescheduled":{"Interview"},
    "Missing Feedback Request":{"Interview","Interview Feedback"},"Job Offer Issued":{"Job Offer"},
    "Appointment Letter Issued":{"Appointment Letter"},"Onboarding Activity Assigned":{"Employee Onboarding","Employee Boarding Activity"},
    "Work Commencement Internal Notice":{"Work Commencement Notice"},
}

def _unique(values): return list(dict.fromkeys(x for x in values if x))
def _parse(value):
    if not value:return []
    if isinstance(value,list):return value
    try:return json.loads(value)
    except Exception:return [x.strip() for x in str(value).replace(";",",").split(",") if x.strip()]
def _user_emails(users): return _unique([frappe.db.get_value("User",u,"email") or u for u in (users or [])])
def _company_from_doc(doc):
    if doc.get("company"):return doc.company
    if doc.get("project"): 
        company=frappe.db.get_value("Project",doc.project,"company")
        if company:return company
    for field in ("job_opening","job_title","qorg_job_opening"):
        if doc.get(field) and frappe.db.exists("Job Opening",doc.get(field)):
            company=frappe.db.get_value("Job Opening",doc.get(field),"company")
            if company:return company
    return frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults","default_company")
def company_branding(company):
    defaults={"company":company,"company_name":company or "Organization","company_logo":"","email_footer":"","reply_to":None,"header":"#176b87","primary":"#176b87","accent":"#d8a51d","light":"#f6f8fa","border":"#dfe3e8","text":"#263238"}
    settings=get_settings()
    if not company or not settings.use_company_branding:return defaults
    doc=frappe.get_doc("Company",company);defaults["company_name"]=doc.get("company_name") or company
    mapping={"company_logo":["company_logo","logo"],"email_footer":["custom_email_footer","email_footer"],"reply_to":["email","default_email"],"header":["custom_print_document_header_color"],"primary":["custom_print_primary_color"],"accent":["custom_print_accent_color"],"light":["custom_print_light_color"],"border":["custom_print_border_color"]}
    for target,fields in mapping.items():
        for field in fields:
            if doc.meta.has_field(field) and doc.get(field):defaults[target]=doc.get(field);break
    return defaults

def _channel_enabled(dt):
    settings=get_settings()
    if dt=="Interview Feedback":return bool(settings.enable_interviewer_notifications)
    if dt in {"Job Applicant","Interview","Job Offer","Appointment Letter"}:return bool(settings.enable_applicant_notifications)
    return bool(settings.enable_recruitment_team_notifications)
def _validate_mapping(notification_type,dt):
    allowed=ALLOWED_REFERENCES.get(notification_type)
    if allowed and dt not in allowed:frappe.throw(_("Notification type {0} cannot be used with {1}.").format(notification_type,dt))
def _recipient_sets(primary=None,cc=None,additional_users=None,confirm_sender=None):
    settings=get_settings();to=_unique(_parse(primary));cc_list=_unique(_parse(cc)+_user_emails(settings.default_cc_users));additional=_user_emails(_parse(additional_users)+list(settings.default_additional_users or []))
    sender=[]
    if confirm_sender is None:confirm_sender=settings.send_sender_confirmation_copy
    if int(confirm_sender or 0):sender=_user_emails([frappe.session.user])
    to=_unique(to+additional+sender);cc_list=[x for x in cc_list if x not in to]
    return {"to":to,"cc":cc_list,"additional_users":additional,"sender_copy":sender}

def preview_recruitment_message(template,reference_doctype,reference_name,primary_recipient=None,cc_json=None,users_json=None,confirm_sender=None,notification_type=None,additional_context=None):
    if not _channel_enabled(reference_doctype):frappe.throw(_("Notifications are disabled for this channel in HR Settings."))
    _validate_mapping(notification_type,reference_doctype)
    doc=frappe.get_doc(reference_doctype,reference_name);doc.check_permission("read")
    sets=_recipient_sets(primary_recipient,cc_json,users_json,confirm_sender)
    if not sets["to"]:frappe.throw(_("At least one primary recipient is required."))
    template_doc=frappe.get_doc("Email Template",template);ctx=doc.as_dict();ctx.update(company_branding(_company_from_doc(doc)));ctx.update(additional_context or {});ctx.update({"reference_doctype":reference_doctype,"reference_name":reference_name,"reference_label":doc.get("title") or doc.get("applicant_name") or doc.get("employee_name") or reference_name,"notification_type":notification_type})
    subject=frappe.render_template(template_doc.subject,ctx);message=frappe.render_template(template_doc.response_html or template_doc.response,ctx)
    return {"template":template,"notification_type":notification_type,"recipients":sets["to"],"cc":sets["cc"],"additional_users":sets["additional_users"],"sender_copy":sets["sender_copy"],"reply_to":ctx.get("reply_to"),"subject":subject,"message":message,"branding":{k:ctx.get(k) for k in ("company_name","company_logo","header","primary","accent","light","border")},"reference_doctype":reference_doctype,"reference_name":reference_name,"requires_confirmation":bool(get_settings().require_recipient_confirmation)}

def send_managed_recruitment_message(notification_type,template,reference_doctype,reference_name,primary_recipient=None,cc_json=None,users_json=None,force=0,additional_context=None):
    preview=preview_recruitment_message(template,reference_doctype,reference_name,primary_recipient,cc_json,users_json,None,notification_type,additional_context)
    raw="|".join([notification_type,reference_doctype,reference_name,template,",".join(sorted(preview["recipients"])),",".join(sorted(preview["cc"]))]);key=hashlib.sha256(raw.encode()).hexdigest()
    existing=frappe.db.get_value("Recruitment Notification Log",{"deduplication_key":key,"delivery_status":"Sent"},"name")
    if existing and not int(force or 0):frappe.throw(_("This notification was already sent. Log: {0}").format(existing))
    values={"doctype":"Recruitment Notification Log","notification_type":notification_type,"reference_doctype":reference_doctype,"reference_name":reference_name,"template":template,"recipients":"\n".join(preview["recipients"]),"subject":preview["subject"],"sent_by":frappe.session.user,"sent_on":now_datetime(),"delivery_status":"Queued","acknowledgement_required":preview["requires_confirmation"],"deduplication_key":key}
    meta=frappe.get_meta("Recruitment Notification Log")
    for field,value in {"cc":"\n".join(preview["cc"]),"additional_users":"\n".join(preview["additional_users"])}.items():
        if meta.has_field(field):values[field]=value
    log=frappe.get_doc(values).insert(ignore_permissions=True)
    try:
        frappe.sendmail(recipients=preview["recipients"],cc=preview["cc"],subject=preview["subject"],message=preview["message"],reference_doctype=reference_doctype,reference_name=reference_name,reply_to=preview["reply_to"],now=True)
        frappe.db.set_value("Recruitment Notification Log",log.name,"delivery_status","Sent",update_modified=False)
    except Exception:
        frappe.db.set_value("Recruitment Notification Log",log.name,{"delivery_status":"Failed","error_message":frappe.get_traceback()},update_modified=False);raise
    return {"log":log.name,"recipients":preview["recipients"],"cc":preview["cc"],"requires_confirmation":preview["requires_confirmation"]}
