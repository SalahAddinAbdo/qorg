from __future__ import annotations

import frappe
from qorg.qorg.enterprise_foundation.idempotent_provisioning import create_custom_fields_if_changed
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

RULES = {
    "critical_risk": ("Critical Project Risk", "Project Risk", "On Save", 0, "A High or Critical project risk requires attention."),
    "risk_review_overdue": ("Risk Review Overdue", "Project Risk", "Daily", 7, "A project risk review date is due or overdue."),
    "deliverable_due_soon": ("Compliance Deliverable Due Soon", "Project Compliance Deliverable", "Daily", 7, "A compliance deliverable is approaching its submission due date."),
    "deliverable_overdue": ("Compliance Deliverable Overdue", "Project Compliance Deliverable", "Daily", 0, "A compliance deliverable has passed its due date without completion."),
    "change_pending_implementation": ("Approved Change Pending Implementation", "Project Change Request", "Daily", 7, "An approved change remains pending implementation."),
    "closure_action_overdue": ("Closure Action Overdue", "Project Closure", "Daily", 7, "A project closure action is overdue."),
    "progress_update_overdue": ("Project Progress Update Overdue", "Project Progress Update", "Daily", 7, "A required project progress update is overdue."),
}


def _notification_message(title, description):
    return f"""<!-- QORG PROJECT NOTIFICATION v2.0 -->
{{% set company_name = doc.get('company') or frappe.defaults.get_user_default('Company') or frappe.db.get_single_value('Global Defaults', 'default_company') or '' %}}
{{% set company_title = frappe.db.get_value('Company', company_name, 'company_name') or company_name or '' %}}
{{% set company_logo = frappe.db.get_value('Company', company_name, 'company_logo') or '' %}}
{{% set primary = frappe.db.get_value('Company', company_name, 'custom_print_primary_color') or '#176B87' %}}
{{% set accent = frappe.db.get_value('Company', company_name, 'custom_print_accent_color') or '#D7A83E' %}}
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F3F6F8;font-family:Arial,Tahoma,sans-serif;color:#253746"><tr><td align="center" style="padding:20px"><table role="presentation" width="720" style="max-width:720px;background:#FFFFFF;border:1px solid #D8E1E6"><tr><td style="background:{{{{ primary }}}};border-bottom:4px solid {{{{ accent }}}};padding:18px 22px;color:#FFFFFF"><table role="presentation" width="100%"><tr><td>{{% if company_logo %}}<img src="{{{{ company_logo }}}}" style="max-height:52px;max-width:180px">{{% else %}}<strong>{{{{ company_title }}}}</strong>{{% endif %}}</td><td align="right"><strong>{title}<br><span dir="rtl">إشعار مشروع</span></strong></td></tr></table></td></tr><tr><td style="padding:24px;line-height:1.65"><div dir="ltr"><p>{description}</p></div><div dir="rtl" style="text-align:right"><p>يتطلب هذا السجل اطلاعكم ومتابعتكم وفقا لإجراءات المشروع المعتمدة.</p></div><table role="presentation" width="100%" style="background:#F7FAFB;border:1px solid #D8E1E6"><tr><td style="padding:8px"><strong>Reference | المرجع</strong></td><td style="padding:8px">{{{{ doc.name }}}}</td></tr><tr><td style="padding:8px"><strong>Status | الحالة</strong></td><td style="padding:8px">{{{{ doc.workflow_state or doc.status or '' }}}}</td></tr></table><p style="text-align:center;margin-top:20px"><a href="{{{{ frappe.utils.get_url_to_form(doc.doctype, doc.name) }}}}" style="background:{{{{ primary }}}};color:#FFFFFF;text-decoration:none;padding:10px 18px;border-radius:5px">Open Record | فتح السجل</a></p></td></tr></table></td></tr></table>"""

CHILD_FIELDS = [
    {"fieldname":"rule_label","label":"Rule Label","fieldtype":"Data","read_only":1,"in_list_view":1,"insert_after":"notification_key"},
    {"fieldname":"description","label":"Description","fieldtype":"Small Text","read_only":1,"insert_after":"rule_label"},
    {"fieldname":"reference_doctype","label":"Reference DocType","fieldtype":"Link","options":"DocType","read_only":1,"in_list_view":1,"insert_after":"description"},
    {"fieldname":"trigger_type","label":"Trigger Type","fieldtype":"Select","options":"On Save\nDaily","read_only":1,"in_list_view":1,"insert_after":"reference_doctype"},
    {"fieldname":"delivery_channel","label":"Delivery Channel","fieldtype":"Select","options":"System Notification\nEmail and System Notification","default":"System Notification","in_list_view":1,"insert_after":"trigger_type"},
    {"fieldname":"recipient_users","label":"Recipient Users","fieldtype":"Small Text","insert_after":"recipient_role","description":"Enter active User IDs or email addresses, separated by commas or new lines."},
    {"fieldname":"recipient_employees","label":"Recipient Employees","fieldtype":"Small Text","insert_after":"recipient_users","description":"Enter Employee IDs, separated by commas or new lines. Each Employee must have Employee.user_id."},
    {"fieldname":"fallback_to_project_manager","label":"Fallback to Project Manager","fieldtype":"Check","default":"1","insert_after":"recipient_employees"},
    {"fieldname":"notification_record","label":"Notification Template","fieldtype":"Link","options":"Notification","read_only":1,"insert_after":"fallback_to_project_manager"},
]

SETTINGS_HELP = [
    {"fieldname":"custom_project_notification_help","label":"How Project Notifications Work","fieldtype":"HTML","options":"<div class='alert alert-info'><b>Project notifications are active policies.</b> Enable a rule, choose one or more Recipient Users, Recipient Employees, or a Recipient Role, then set the delivery channel. Due Soon Days is used by scheduled rules. The linked Notification Template controls the editable subject and message. If no recipient is configured, the engine may fall back to the Project Manager when enabled.</div>","insert_after":"custom_project_notification_rules_section"},
]


def _ensure_template(key, label, doctype, description):
    name="QOrg - "+label
    if frappe.db.exists("Notification",name):
        return name
    meta=frappe.get_meta("Notification")
    data={
        "doctype":"Notification","name":name,"subject":label+" - {{ doc.name }}",
        "document_type":doctype,"event":"Save","enabled":0,
        "condition":"False",
        "message": _notification_message(label, description),
        "channel":"System Notification",
    }
    data={k:v for k,v in data.items() if k in ("doctype","name") or meta.has_field(k)}
    doc=frappe.get_doc(data)
    if doc.meta.has_field("recipients"):
        doc.append("recipients",{"receiver_by_role":"System Manager"})
    doc.insert(ignore_permissions=True)
    return name



def _repair_recipient_fields():
    """Replace unsupported nested Table fields in the child rule DocType."""
    for fieldname in ("recipient_users", "recipient_employees"):
        custom_name="Project Notification Rule-"+fieldname
        if not frappe.db.exists("Custom Field",custom_name):
            continue
        fieldtype=frappe.db.get_value("Custom Field",custom_name,"fieldtype")
        if fieldtype=="Table":
            frappe.delete_doc("Custom Field",custom_name,ignore_permissions=True,force=True)

def provision_project_notifications():
    _repair_recipient_fields()
    if not frappe.db.exists("DocType","Project Notification Rule"):
        return
    create_custom_fields_if_changed({"Project Notification Rule":CHILD_FIELDS,"Projects Settings":SETTINGS_HELP},update=True)
    if frappe.get_meta("Project Notification Rule").has_field("recipient_employee_field"):
        make_property_setter("Project Notification Rule", "recipient_employee_field", "hidden", 1, "Check", validate_fields_for_doctype=False)
    make_property_setter("Projects Settings", "project_notification_rules", "read_only", 0, "Check", validate_fields_for_doctype=False)
    for editable_field in (
        "delivery_channel", "enabled", "due_soon_days", "recipient_role",
        "recipient_users", "recipient_employees", "fallback_to_project_manager",
    ):
        if frappe.get_meta("Project Notification Rule").has_field(editable_field):
            make_property_setter("Project Notification Rule", editable_field, "read_only", 0, "Check", validate_fields_for_doctype=False)
    settings=frappe.get_single("Projects Settings")
    existing={row.notification_key:row for row in settings.get("project_notification_rules") or []}
    for key, spec in RULES.items():
        label, doctype, trigger, days, description=spec
        row=existing.get(key)
        if not row:
            row=settings.append("project_notification_rules",{"notification_key":key,"enabled":1,"due_soon_days":days})
        row.rule_label=label
        row.description=description
        row.reference_doctype=doctype if frappe.db.exists("DocType",doctype) else ""
        row.trigger_type=trigger
        if not row.delivery_channel: row.delivery_channel="System Notification"
        row.fallback_to_project_manager=1 if row.get("fallback_to_project_manager") is None else row.fallback_to_project_manager
        if frappe.db.exists("DocType",doctype): row.notification_record=_ensure_template(key,label,doctype,description)
    settings.save(ignore_permissions=True)
    frappe.clear_cache(doctype="Projects Settings")
    audit_project_notification_configuration()


def audit_project_notification_configuration():
    if not frappe.db.exists("DocType", "Project Notification Rule"):
        return True
    settings = frappe.get_single("Projects Settings")
    failures = []
    rows = {row.notification_key: row for row in settings.get("project_notification_rules") or []}
    for key, spec in RULES.items():
        row = rows.get(key)
        if not row:
            failures.append(f"{key}: missing rule row")
            continue
        expected_doctype = spec[1]
        expected_trigger = spec[2]
        if row.reference_doctype != expected_doctype:
            failures.append(f"{key}: reference_doctype")
        if row.trigger_type != expected_trigger:
            failures.append(f"{key}: trigger_type")
        if not row.notification_record or not frappe.db.exists("Notification", row.notification_record):
            failures.append(f"{key}: notification_record")
    if failures:
        frappe.throw("Invalid project notification configuration: " + "; ".join(failures))
    return True
