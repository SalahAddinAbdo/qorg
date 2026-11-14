from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import get_url_to_form
from frappe.utils.jinja import render_template

TEMPLATE_VERSION = "QORG-MANAGED-COMMUNICATION-v3.0"
DEFAULT_PRIMARY = "#176B87"
DEFAULT_ACCENT = "#D7A83E"

TEMPLATES = {
    "Procurement Complaint Acknowledgement": ("Procurement Complaint", "Complaint Acknowledgement | تأكيد استلام الشكوى", "Your procurement complaint has been received and registered for confidential review.", "تم استلام شكوى المشتريات وتسجيلها للمراجعة السرية."),
    "Approved Purchase Request": ("Material Request", "Approved Purchase Request | طلب شراء معتمد", "An approved purchase request requires procurement action.", "يتطلب طلب الشراء المعتمد بدء إجراء المشتريات."),
    "Procurement Process Assignment": ("Procurement Process", "Procurement Process Assignment | تكليف بعملية مشتريات", "A procurement process has been assigned for setup and follow-up.", "تم تكليفكم بإعداد ومتابعة عملية المشتريات."),
    "Procurement Invitation": ("Procurement Notice", "Invitation to Participate | دعوة للمشاركة", "You are invited to review the procurement documents and submit a complete offer before the deadline.", "ندعوكم لمراجعة وثائق المنافسة وتقديم عرض مكتمل قبل الموعد النهائي."),
    "Submission Deadline Reminder": ("Procurement Notice", "Submission Deadline Reminder | تذكير بموعد الإغلاق", "The submission deadline is approaching.", "يقترب الموعد النهائي لتقديم العرض."),
    "Bid Submission Receipt": ("Procurement Submission", "Submission Receipt | إشعار استلام العرض", "Your submission was received and registered successfully.", "تم استلام عرضكم وتسجيله بنجاح."),
    "Supplier Information Request": ("Supplier Registration", "Additional Information Required | مطلوب معلومات إضافية", "Additional supplier information or evidence is required.", "يلزم تقديم معلومات أو أدلة إضافية عن المورد."),
    "Supplier Profile Approved": ("Supplier Registration", "Supplier Profile Approved | اعتماد ملف المورد", "The supplier profile passed the required review.", "اجتاز ملف المورد المراجعة المطلوبة."),
    "Supplier Profile Rejected": ("Supplier Registration", "Supplier Profile Decision | قرار بشأن ملف المورد", "The supplier profile could not be approved in its current form.", "تعذر اعتماد ملف المورد بصورته الحالية."),
    "Award Recommendation Submitted": ("Procurement Process", "Award Recommendation Submitted | رفع توصية الترسية", "The award recommendation is ready for review.", "توصية الترسية جاهزة للمراجعة."),
    "Award Notification": ("Procurement Process", "Award Notification | إشعار الترسية", "A procurement award decision has been approved.", "تم اعتماد قرار ترسية المشتريات."),
    "Unsuccessful Bidder Notice": ("Procurement Submission", "Bid Outcome Notice | إشعار بنتيجة العرض", "The submitted offer was not selected for award.", "لم يتم اختيار العرض المقدم للترسية."),
    "Contract Approval Required": ("Procurement Contract", "Contract Approval Required | مطلوب اعتماد العقد", "A procurement contract is awaiting approval.", "يوجد عقد مشتريات بانتظار الاعتماد."),
    "Contract Activated": ("Procurement Contract", "Contract Activated | تفعيل العقد", "The procurement contract is now active.", "أصبح عقد المشتريات فعالا."),
    "Receipt Inspection Required": ("Purchase Receipt", "Receipt Inspection Required | مطلوب فحص الاستلام", "A purchase receipt requires inspection before acceptance.", "يتطلب استلام المشتريات فحصا قبل القبول."),
    "Receipt Acceptance Notice": ("Purchase Receipt", "Receipt Acceptance Notice | إشعار قبول الاستلام", "The receipt acceptance status has been updated.", "تم تحديث حالة قبول الاستلام."),
    "Stock Handover Notice": ("Stock Handover", "Stock Handover Notice | إشعار تسليم مخزني", "A stock handover requires acknowledgement.", "يتطلب التسليم المخزني إقرارا بالاستلام."),
    "Handover Discrepancy Notice": ("Stock Handover", "Handover Discrepancy | فروقات في التسليم", "A stock handover discrepancy requires review.", "توجد فروقات في التسليم المخزني تتطلب المراجعة."),
    "Asset Custody Notice": ("Asset Custody", "Asset Custody Notice | إشعار عهدة أصل", "An asset custody record requires acknowledgement or action.", "يتطلب سجل عهدة الأصل الإقرار أو اتخاذ إجراء."),
    "Custody Assignment Notice": ("Asset Custody", "Custody Assignment | إشعار عهدة", "An asset custody record has been assigned.", "تم إسناد سجل عهدة."),
    "Custody Return Reminder": ("Asset Custody", "Custody Return Reminder | تذكير بإرجاع العهدة", "The expected custody return date is approaching or overdue.", "يقترب موعد إرجاع العهدة أو تجاوز الموعد."),
    "Asset Incident Notice": ("Asset Incident", "Asset Incident Notice | إشعار حادث أصل", "An asset incident has been registered and requires review.", "تم تسجيل حادث أصل ويتطلب المراجعة."),
    "Incident Decision Pending": ("Asset Incident", "Incident Decision Pending | قرار حادث أصل معلق", "An asset incident requires a decision.", "يتطلب حادث الأصل اتخاذ قرار."),
    "Verification Approval Pending": ("Physical Verification", "Verification Approval Pending | اعتماد الجرد معلق", "A physical verification requires approval.", "يتطلب الجرد الفعلي الاعتماد."),
    "Verification Approval Notice": ("Physical Verification", "Verification Approval Notice | إشعار اعتماد الجرد", "A physical verification is ready for approval.", "الجرد الفعلي جاهز للاعتماد."),
}


def body(title_en, title_ar, lead_en, lead_ar):
    # Use safe fixed inline colors in stored templates. Company identity remains dynamic.
    return f'''<!-- {TEMPLATE_VERSION} -->
{{% set company_name = doc.get("company") or frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company") %}}
{{% set company_title = frappe.db.get_value("Company", company_name, "company_name") or company_name or "" %}}
{{% set company_logo = frappe.db.get_value("Company", company_name, "company_logo") or "" %}}
{{% set primary = frappe.db.get_value("Company", company_name, "custom_print_primary_color") or "#176B87" %}}
{{% set accent = frappe.db.get_value("Company", company_name, "custom_print_accent_color") or "#D7A83E" %}}
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#F4F7F8;font-family:Arial,Tahoma,sans-serif;color:#243342"><tr><td align="center" style="padding:24px 10px">
<table role="presentation" width="760" cellpadding="0" cellspacing="0" style="max-width:760px;background-color:#FFFFFF;border:1px solid #D9E2E6">
<tr><td style="background-color:{{{{ primary }}}};border-bottom:4px solid {{{{ accent }}}};padding:20px 24px;color:#FFFFFF">
<table role="presentation" width="100%"><tr><td>{{% if company_logo %}}<img src="{{{{ company_logo }}}}" alt="{{{{ company_title }}}}" style="display:block;max-height:56px;max-width:190px">{{% else %}}<strong>{{{{ company_title }}}}</strong>{{% endif %}}</td><td align="right"><strong>{title_en}<br><span dir="rtl">{title_ar}</span></strong></td></tr></table>
</td></tr><tr><td style="padding:26px;line-height:1.65"><div dir="ltr"><p>Dear Recipient,</p><p>{lead_en}</p></div><hr style="border:0;border-top:1px solid #E1E7EB"><div dir="rtl" style="text-align:right"><p>السيد/السيدة المستلم المحترم،</p><p>{lead_ar}</p></div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#F7FAFB;border:1px solid #D9E2E6"><tr><td style="padding:8px"><strong>Reference | المرجع</strong></td><td style="padding:8px">{{{{ doc.name }}}}</td></tr><tr><td style="padding:8px"><strong>Status | الحالة</strong></td><td style="padding:8px">{{{{ doc.workflow_state or doc.status or doc.submission_status or doc.registration_status or doc.handover_status or doc.custody_status or doc.custom_receipt_acceptance_status or "" }}}}</td></tr></table>
<p style="text-align:center;margin-top:22px"><a href="{{{{ record_url or frappe.utils.get_url_to_form(doc.doctype, doc.name) }}}}" style="display:inline-block;background-color:{{{{ primary }}}};color:#FFFFFF;text-decoration:none;padding:10px 20px;border-radius:5px;font-weight:bold">Open Record | فتح السجل</a></p>
<p style="font-size:12px;color:#667780;text-align:center">Official communication from {{{{ company_title }}}}.<br><span dir="rtl">مراسلة رسمية صادرة عن {{{{ company_title }}}}.</span></p></td></tr></table></td></tr></table>'''


def _body_field():
    meta = frappe.get_meta("Email Template")
    if meta.has_field("response_html"):
        return "response_html"
    return "response"


def _write_raw_template(name, reference_doctype, subject, message):
    fieldname = _body_field()
    existing = frappe.db.exists("Email Template", name)
    doc = frappe.get_doc("Email Template", name) if existing else frappe.new_doc("Email Template")
    if not existing:
        doc.name = name
    doc.subject = subject
    doc.use_html = 1
    if doc.meta.has_field("reference_doctype"):
        doc.reference_doctype = reference_doctype
    # Insert/save without the HTML body, then write raw HTML directly to avoid Text Editor sanitization.
    doc.set(fieldname, "")
    doc.save(ignore_permissions=True) if existing else doc.insert(ignore_permissions=True)
    values = {fieldname: message, "use_html": 1, "subject": subject}
    if fieldname == "response_html" and doc.meta.has_field("response"):
        values["response"] = ""
    if doc.meta.has_field("reference_doctype"):
        values["reference_doctype"] = reference_doctype
    frappe.db.set_value("Email Template", name, values, update_modified=False)


def upsert_templates():
    for name, (reference_doctype, subject, lead_en, lead_ar) in TEMPLATES.items():
        _write_raw_template(name, reference_doctype, subject + " - {{ doc.name }}", body(subject.split(" | ")[0], subject.split(" | ")[-1], lead_en, lead_ar))


def audit_managed_templates():
    fieldname = _body_field()
    failures = []
    for name in TEMPLATES:
        from html import unescape
        stored = frappe.db.get_value("Email Template", name, fieldname) or ""
        message = unescape(stored)
        if "background:{" in message or TEMPLATE_VERSION not in message or "<table" not in message:
            failures.append(name)
    if failures:
        frappe.throw(_("Managed Email Templates are malformed: {0}").format(", ".join(failures)))
    return True


def render(template_name, doctype, name):
    frappe.has_permission(doctype, "read", name, throw=True)
    doc = frappe.get_doc(doctype, name)
    template = frappe.get_doc("Email Template", template_name)
    context = {"doc": doc, "record_url": get_url_to_form(doctype, name)}
    return {"subject": render_template(template.subject, context), "message": render_template(template.get(_body_field()) or "", context)}


@frappe.whitelist()
def preview(template_name, doctype, name):
    return render(template_name, doctype, name)


@frappe.whitelist()
def send(template_name, doctype, name, recipients, cc=None):
    result = render(template_name, doctype, name)
    recipients = [x.strip() for x in (recipients or "").replace(";", ",").split(",") if x.strip()]
    if not recipients:
        frappe.throw(_("At least one recipient is required."))
    frappe.sendmail(recipients=recipients, cc=cc, subject=result["subject"], message=result["message"], reference_doctype=doctype, reference_name=name, now=True)
    return {"sent": True}


def provision_email_templates():
    upsert_templates()
    audit_managed_templates()


def _allowed_template(reference_doctype, template_name):
    if template_name not in TEMPLATES or TEMPLATES[template_name][0] != reference_doctype:
        frappe.throw(_("Template {0} is not allowed for {1}.").format(template_name, reference_doctype))


@frappe.whitelist()
def preview_template(reference_doctype, reference_name, template_name):
    _allowed_template(reference_doctype, template_name)
    return preview(template_name, reference_doctype, reference_name)


@frappe.whitelist()
def send_template(reference_doctype, reference_name, template_name, recipients, cc=None):
    _allowed_template(reference_doctype, template_name)
    return send(template_name, reference_doctype, reference_name, recipients, cc)
