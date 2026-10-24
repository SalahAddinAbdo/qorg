import json
import frappe
from frappe import _
from .settings import get_settings

def _emails(users):
    out=[]
    for user in users or []:
        email=frappe.db.get_value("User",user,"email") or user
        if email and email not in out: out.append(email)
    return out

def company_branding(company):
    s=get_settings();defaults={"company":company,"reply_to":None,"header":"#176b87","primary":"#176b87","accent":"#d8a51d","light":"#f6f8fa","border":"#dfe3e8"}
    if not company or not s.use_company_branding:return defaults
    names=["email","custom_print_document_header_color","custom_print_primary_color","custom_print_accent_color","custom_print_light_color","custom_print_border_color"]
    names=[x for x in names if frappe.get_meta("Company").has_field(x)]
    data=frappe.db.get_value("Company",company,names,as_dict=True) or {}
    defaults.update({"reply_to":data.get("email"),"header":data.get("custom_print_document_header_color") or defaults["header"],"primary":data.get("custom_print_primary_color") or defaults["primary"],"accent":data.get("custom_print_accent_color") or defaults["accent"],"light":data.get("custom_print_light_color") or defaults["light"],"border":data.get("custom_print_border_color") or defaults["border"]})
    return defaults

def _channel_enabled(reference_doctype):
    s=get_settings()
    if reference_doctype in {"Interview Feedback"}:return bool(s.enable_interviewer_notifications)
    if reference_doctype in {"Job Applicant","Interview","Job Offer","Appointment Letter"}:return bool(s.enable_applicant_notifications)
    return bool(s.enable_recruitment_team_notifications)

def recipients(primary=None,cc=None,additional_users=None,confirm_sender=None):
    s=get_settings();out=[]
    for value in [primary]+list(cc or [])+_emails(s.default_cc_users):
        if value and value not in out:out.append(value)
    for value in _emails(list(additional_users or [])+list(s.default_additional_users)):
        if value not in out:out.append(value)
    if confirm_sender is None:confirm_sender=bool(s.send_confirmation_copy_sender)
    if confirm_sender:
        email=frappe.db.get_value("User",frappe.session.user,"email")
        if email and email not in out:out.append(email)
    return out

@frappe.whitelist()
def preview_recruitment_message(template,reference_doctype,reference_name,primary_recipient=None,cc_json=None,users_json=None,confirm_sender=None):
    if not _channel_enabled(reference_doctype):frappe.throw(_("This notification channel is disabled in HR Settings."))
    doc=frappe.get_doc(reference_doctype,reference_name);doc.check_permission("read")
    rec=recipients(primary_recipient,json.loads(cc_json or "[]"),json.loads(users_json or "[]"),confirm_sender)
    if not rec:frappe.throw(_("At least one recipient is required."))
    s=get_settings()
    return {"template":template,"recipients":rec,"reply_to":company_branding(doc.get("company")).get("reply_to"),"requires_confirmation":bool(s.require_recipient_confirmation),"reference":f"{reference_doctype}: {reference_name}"}

@frappe.whitelist(methods=["POST"])
def send_recruitment_message(template,reference_doctype,reference_name,primary_recipient=None,cc_json=None,users_json=None,confirm_sender=None):
    preview=preview_recruitment_message(template,reference_doctype,reference_name,primary_recipient,cc_json,users_json,confirm_sender)
    doc=frappe.get_doc(reference_doctype,reference_name);et=frappe.get_doc("Email Template",template);ctx=doc.as_dict();ctx.update(company_branding(doc.get("company")));ctx["recipient_confirmation_required"]=preview["requires_confirmation"]
    frappe.sendmail(recipients=preview["recipients"],subject=frappe.render_template(et.subject,ctx),message=frappe.render_template(et.response_html or et.response,ctx),reference_doctype=reference_doctype,reference_name=reference_name,reply_to=preview["reply_to"],now=True)
    return preview



def send_managed_recruitment_message(notification_type,template,reference_doctype,reference_name,primary_recipient=None,cc_json=None,users_json=None,force=0):
    import hashlib
    preview=preview_recruitment_message(template,reference_doctype,reference_name,primary_recipient,cc_json,users_json,None)
    recipient_key=",".join(sorted(preview["recipients"]));raw=f"{notification_type}|{reference_doctype}|{reference_name}|{template}|{recipient_key}"
    key=hashlib.sha256(raw.encode()).hexdigest()
    existing=frappe.db.get_value("Recruitment Notification Log",{"deduplication_key":key,"delivery_status":"Sent"},"name")
    if existing and not int(force or 0):frappe.throw(_("This notification was already sent. Log: {0}").format(existing))
    doc=frappe.get_doc(reference_doctype,reference_name);et=frappe.get_doc("Email Template",template);ctx=doc.as_dict();ctx.update(company_branding(doc.get("company")));ctx["recipient_confirmation_required"]=preview["requires_confirmation"]
    subject=frappe.render_template(et.subject,ctx);message=frappe.render_template(et.response_html or et.response,ctx)
    log=frappe.get_doc({"doctype":"Recruitment Notification Log","notification_type":notification_type,"reference_doctype":reference_doctype,"reference_name":reference_name,"template":template,"recipients":"\n".join(preview["recipients"]),"subject":subject,"sent_by":frappe.session.user,"sent_on":frappe.utils.now_datetime(),"delivery_status":"Queued","acknowledgement_required":preview["requires_confirmation"],"deduplication_key":key})
    log.insert(ignore_permissions=True)
    try:
        frappe.sendmail(recipients=preview["recipients"],subject=subject,message=message,reference_doctype=reference_doctype,reference_name=reference_name,reply_to=preview["reply_to"],now=True)
        frappe.db.set_value("Recruitment Notification Log",log.name,"delivery_status","Sent",update_modified=False)
        if reference_doctype=="Job Applicant":frappe.db.set_value("Job Applicant",reference_name,{"qorg_last_notification_type":notification_type,"qorg_last_notification_on":frappe.utils.now_datetime()},update_modified=False)
    except Exception:
        frappe.db.set_value("Recruitment Notification Log",log.name,{"delivery_status":"Failed","error_message":frappe.get_traceback()},update_modified=False);raise
    return {"log":log.name,"recipients":preview["recipients"],"requires_confirmation":preview["requires_confirmation"]}
