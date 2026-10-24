import hashlib
import json
import frappe
from frappe import _
from frappe.utils import now_datetime

def _emails(value):
    if not value:return []
    if isinstance(value,list):items=value
    else:
        try:items=json.loads(value)
        except Exception:items=[x.strip() for x in str(value).replace(";",",").split(",")]
    return [x for x in items if x]

def company_branding(reference):
    company=reference.get("company")
    if not company and reference.get("project"):company=frappe.db.get_value("Project",reference.project,"company")
    if not company:company=frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults","default_company")
    values={"company":company,"company_name":company or "Organization","company_logo":"","primary_color":"#176b87","secondary_color":"#a8d3df","accent_color":"#236b3d","background_color":"#eef2f5","text_color":"#263238","border_color":"#d9e1e5","footer_text":"","reply_to":None}
    if company and frappe.db.exists("Company",company):
        doc=frappe.get_doc("Company",company);values["company_name"]=doc.company_name or company
        for target,candidates in {"company_logo":["company_logo","logo"],"primary_color":["custom_primary_color","primary_color"],"secondary_color":["custom_secondary_color","secondary_color"],"accent_color":["custom_accent_color","accent_color"],"footer_text":["custom_email_footer","email_footer"],"reply_to":["email","default_email"]}.items():
            for field in candidates:
                if doc.meta.has_field(field) and doc.get(field):values[target]=doc.get(field);break
    return values

def preview_participation_message(notification_type,template,reference_doctype,reference_name,primary_recipient=None,cc_json=None,users_json=None):
    reference=frappe.get_doc(reference_doctype,reference_name);reference.check_permission("read")
    person=None
    if reference.get("external_person") and frappe.db.exists("External Person",reference.external_person):person=frappe.get_doc("External Person",reference.external_person)
    primary=primary_recipient or (person.get("primary_email") if person else None)
    recipients=_emails(primary)+[frappe.db.get_value("User",u,"email") or u for u in _emails(users_json)]
    recipients=list(dict.fromkeys(x for x in recipients if x))
    if not recipients:frappe.throw(_("At least one recipient is required."))
    template_doc=frappe.get_doc("Email Template",template);context=reference.as_dict();context.update(company_branding(reference));context["notification_type"]=notification_type
    return {"recipients":recipients,"cc":_emails(cc_json),"subject":frappe.render_template(template_doc.subject,context),"message":frappe.render_template(template_doc.response_html or template_doc.response,context),"reply_to":context.get("reply_to"),"context":context}

def send_participation_message(notification_type,template,reference_doctype,reference_name,primary_recipient=None,cc_json=None,users_json=None,force=0):
    preview=preview_participation_message(notification_type,template,reference_doctype,reference_name,primary_recipient,cc_json,users_json)
    raw="|".join([notification_type,reference_doctype,reference_name,template,",".join(sorted(preview["recipients"]))]);key=hashlib.sha256(raw.encode()).hexdigest()
    log_dt="Recruitment Notification Log"
    existing=frappe.db.get_value(log_dt,{"deduplication_key":key,"delivery_status":"Sent"},"name") if frappe.db.exists("DocType",log_dt) else None
    if existing and not int(force or 0):frappe.throw(_("This notification was already sent. Log: {0}").format(existing))
    log=None
    if frappe.db.exists("DocType",log_dt):
        log=frappe.get_doc({"doctype":log_dt,"notification_type":notification_type,"reference_doctype":reference_doctype,"reference_name":reference_name,"template":template,"recipients":"\n".join(preview["recipients"]),"cc":"\n".join(preview["cc"]),"subject":preview["subject"],"sent_by":frappe.session.user,"sent_on":now_datetime(),"delivery_status":"Queued","deduplication_key":key}).insert(ignore_permissions=True)
    try:
        frappe.sendmail(recipients=preview["recipients"],cc=preview["cc"],subject=preview["subject"],message=preview["message"],reference_doctype=reference_doctype,reference_name=reference_name,reply_to=preview["reply_to"],now=True)
        if log:frappe.db.set_value(log_dt,log.name,"delivery_status","Sent",update_modified=False)
    except Exception:
        if log:frappe.db.set_value(log_dt,log.name,{"delivery_status":"Failed","error_message":frappe.get_traceback()},update_modified=False)
        raise
    return {"log":log.name if log else None,"recipients":preview["recipients"],"cc":preview["cc"]}
