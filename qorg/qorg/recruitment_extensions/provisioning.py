from pathlib import Path
import hashlib
import json
import os
import frappe
from qorg.qorg.enterprise_foundation.idempotent_provisioning import create_custom_fields_if_changed
from .constants import CONFIGURATION_VERSION

LEGACY_RECRUITMENT_TEMPLATES = (
    "Recruitment Application Decision",
    "Recruitment Offer Issued",
    "Recruitment Interview Invitation",
)


def _template_hash(subject,response_html,use_html):
    payload={"subject":subject or "","response_html":response_html or "","use_html":int(use_html or 0)}
    return hashlib.sha256(json.dumps(payload,sort_keys=True,ensure_ascii=False).encode()).hexdigest()

def provision_recruitment_extensions():
    _custom_fields()
    result=_email_templates()
    _reference_check_print_format()
    result["deleted_legacy"]=_delete_legacy_templates()
    from .layout_provisioning import reconcile_recruitment_form_layouts
    reconcile_recruitment_form_layouts()
    reconcile_standard_reports()
    frappe.clear_cache()
    return result

def _delete_legacy_templates():
    deleted=[]
    for name in LEGACY_RECRUITMENT_TEMPLATES:
        if frappe.db.exists("Email Template",name):
            frappe.delete_doc("Email Template",name,ignore_permissions=True,force=True)
            deleted.append(name)
    return deleted

def _custom_fields():
    path=frappe.get_app_path("qorg","qorg","recruitment_extensions","data","custom_fields.json")
    rows=json.load(open(path,encoding="utf-8"));grouped={}
    for row in rows:
        row=dict(row);dt=row.pop("dt");grouped.setdefault(dt,[]).append(row)
    for dt,definitions in grouped.items():
        if frappe.db.exists("DocType",dt):create_custom_fields_if_changed({dt:definitions},update=True)

def _email_templates():
    folder=frappe.get_app_path("qorg","qorg","recruitment_extensions","data","email_templates")
    hashes_path=frappe.get_app_path("qorg","qorg","recruitment_extensions","data","managed_template_hashes.json")
    known=json.load(open(hashes_path,encoding="utf-8")) if os.path.exists(hashes_path) else {}
    result={"created":[],"upgraded":[],"preserved_manual":[],"unchanged":[]}
    for filename in sorted(os.listdir(folder)):
        if not filename.endswith(".json"):continue
        data=json.load(open(os.path.join(folder,filename),encoding="utf-8"));name=data["name"]
        new_hash=_template_hash(data.get("subject"),data.get("response_html") or data.get("response"),data.get("use_html"))
        if not frappe.db.exists("Email Template",name):
            frappe.get_doc(data).insert(ignore_permissions=True);result["created"].append(name);continue
        template=frappe.get_doc("Email Template",name)
        current_hash=_template_hash(template.subject,template.response_html or template.response,template.use_html)
        if current_hash==new_hash:
            result["unchanged"].append(name);continue
        managed_flag=template.meta.has_field("qorg_managed_template") and template.get("qorg_managed_template")
        recognized=current_hash in set(known.get(name) or [])
        if managed_flag or recognized:
            template.subject=data.get("subject");template.response_html=data.get("response_html") or data.get("response");template.response=data.get("response");template.use_html=data.get("use_html",1)
            if template.meta.has_field("qorg_managed_template"):template.qorg_managed_template=1
            if template.meta.has_field("qorg_managed_hash"):template.qorg_managed_hash=new_hash
            template.flags.ignore_permissions=True;template.save();result["upgraded"].append(name)
        else:
            result["preserved_manual"].append(name)
    return result

def reconcile_standard_reports():
    names=("Applicant Screening and Aging","Candidate Selection Queue","External Opportunity Overview","Interview Progress","Offer and Appointment Tracking","Recruitment Cycle Performance","Recruitment Pipeline")
    for name in names:
        if frappe.db.exists("Report",name):
            frappe.db.set_value("Report",name,{"disabled":0,"is_standard":"Yes"},update_modified=False)
    frappe.clear_cache()

@frappe.whitelist()
def audit_reports_and_templates():
    if frappe.session.user!="Administrator":frappe.throw("Administrator only",frappe.PermissionError)
    folder=frappe.get_app_path("qorg","qorg","recruitment_extensions","data","email_templates")
    result={"templates":{},"reports":{},"asset_build_required":True}
    for filename in sorted(os.listdir(folder)):
        if not filename.endswith(".json"):continue
        data=json.load(open(os.path.join(folder,filename),encoding="utf-8"));name=data["name"]
        if not frappe.db.exists("Email Template",name):result["templates"][name]="Missing";continue
        template=frappe.get_doc("Email Template",name)
        expected=_template_hash(data.get("subject"),data.get("response_html") or data.get("response"),data.get("use_html"))
        actual=_template_hash(template.subject,template.response_html or template.response,template.use_html)
        result["templates"][name]="Current" if actual==expected else "Customized or Old"
    for name in ("Applicant Screening and Aging","Candidate Selection Queue","External Opportunity Overview","Interview Progress","Offer and Appointment Tracking","Recruitment Cycle Performance","Recruitment Pipeline"):
        result["reports"][name]="Current record" if frappe.db.exists("Report",name) else "Missing"
    return result



def _reference_check_print_format():
    questionnaire_name = "Candidate Reference Check Questionnaire - Bilingual"
    template_path = frappe.get_app_path("qorg", "qorg", "recruitment_extensions", "templates", "candidate_reference_check_questionnaire.html")
    html = Path(template_path).read_text(encoding="utf-8")
    values = {
        "doc_type": "Candidate Reference Check", "print_format_type": "Jinja",
        "html": html, "standard": "No", "disabled": 0,
    }
    if frappe.db.exists("Print Format", questionnaire_name):
        frappe.db.set_value("Print Format", questionnaire_name, values, update_modified=False)
    else:
        frappe.get_doc({"doctype": "Print Format", "name": questionnaire_name, **values}).insert(ignore_permissions=True)

    if frappe.get_meta("Print Settings").has_field("qorg_rules"):
        settings = frappe.get_single("Print Settings")
        if not any(row.document_type == "Candidate Reference Check" for row in settings.get("qorg_rules") or []):
            settings.append("qorg_rules", {
                "document_type": "Candidate Reference Check", "enabled": 1,
                "print_profile": "Q Universal", "set_as_default": 1,
                "include_letter_head": 1, "include_workflow_status": 1,
                "include_signatures": 1, "include_audit_information": 1,
                "include_attachments": 1,
            })
            settings.save(ignore_permissions=True)
        from qorg.printing.provisioning import provision_universal_print_formats
        provision_universal_print_formats(force=True)
