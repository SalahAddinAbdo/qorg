from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import get_url_to_form
from frappe.utils.jinja import render_template

MARKER = "<!-- QORG PROCUREMENT INVENTORY V2 -->"


def _company(doc):
    name = doc.get("company") or frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company")
    if not name:
        return frappe._dict(name="", title="", logo="", primary="#176B87", accent="#D7A83E", light="#EAF3F6", border="#C9D6DC")
    values = frappe.db.get_value("Company", name, ["company_name", "company_logo", "custom_print_primary_color", "custom_print_accent_color", "custom_print_light_color", "custom_print_border_color"], as_dict=True) or {}
    return frappe._dict(name=name, title=values.get("company_name") or name, logo=values.get("company_logo") or "", primary=values.get("custom_print_primary_color") or "#176B87", accent=values.get("custom_print_accent_color") or "#D7A83E", light=values.get("custom_print_light_color") or "#EAF3F6", border=values.get("custom_print_border_color") or "#C9D6DC")


def body(title_en, title_ar, lead_en, lead_ar):
    return MARKER + f'''{{% set company_name = doc.get("company") or frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company") %}}
{{% set company_title = frappe.db.get_value("Company", company_name, "company_name") or company_name or "" %}}
{{% set company_logo = frappe.db.get_value("Company", company_name, "company_logo") or "" %}}
{{% set primary = frappe.db.get_value("Company", company_name, "custom_print_primary_color") or "#176B87" %}}
{{% set accent = frappe.db.get_value("Company", company_name, "custom_print_accent_color") or "#D7A83E" %}}
<div style="margin:0;background:#f4f7f8;padding:24px 10px;font-family:Arial,Tahoma,sans-serif;color:#243342;line-height:1.65">
<div style="max-width:760px;margin:auto;background:#fff;border:1px solid #d9e2e6;border-radius:10px;overflow:hidden">
<div style="background:{{{{ primary }}}};color:#fff;padding:20px 24px;border-bottom:4px solid {{{{ accent }}}}"><table width="100%"><tr><td>{{% if company_logo %}}<img src="{{{{ company_logo }}}}" alt="{{{{ company_title }}}}" style="max-height:56px;max-width:190px">{{% else %}}<b>{{{{ company_title }}}}</b>{{% endif %}}</td><td align="right"><b>{title_en}<br><span dir="rtl">{title_ar}</span></b></td></tr></table></div>
<div style="padding:26px"><div dir="ltr"><p>Dear Recipient,</p><p>{lead_en}</p></div><hr style="border:0;border-top:1px solid #e1e7eb"><div dir="rtl" style="text-align:right"><p>السيد/السيدة المستلم المحترم،</p><p>{lead_ar}</p></div>
<table width="100%" style="border-collapse:collapse;background:#f7fafb;border:1px solid #d9e2e6"><tr><td style="padding:8px"><b>Reference | المرجع</b></td><td style="padding:8px">{{{{ doc.name }}}}</td></tr><tr><td style="padding:8px"><b>Status | الحالة</b></td><td style="padding:8px">{{{{ doc.workflow_state or doc.status or doc.submission_status or doc.registration_status or doc.handover_status or doc.custody_status or doc.custom_receipt_acceptance_status or "" }}}}</td></tr></table>
<p style="text-align:center;margin-top:22px"><a href="{{{{ record_url or frappe.utils.get_url_to_form(doc.doctype, doc.name) }}}}" style="display:inline-block;background:{{{{ primary }}}};color:#fff;text-decoration:none;padding:10px 20px;border-radius:5px;font-weight:bold">Open Record | فتح السجل</a></p>
<p style="font-size:12px;color:#667780;text-align:center">Official communication from {{{{ company_title }}}}.<br><span dir="rtl">مراسلة رسمية صادرة عن {{{{ company_title }}}}.</span></p></div></div></div>'''


TEMPLATES = {
    "Approved Purchase Request": ("Approved Purchase Request | طلب شراء معتمد", "An approved purchase request requires procurement action.", "يتطلب طلب الشراء المعتمد بدء إجراء المشتريات."),
    "Procurement Process Assignment": ("Procurement Process Assignment | تكليف بعملية مشتريات", "A procurement process has been assigned for setup and follow-up.", "تم تكليفكم بإعداد ومتابعة عملية المشتريات."),
    "Procurement Invitation": ("Invitation to Participate | دعوة للمشاركة", "You are invited to review the procurement documents and submit a complete offer before the deadline.", "ندعوكم لمراجعة وثائق المنافسة وتقديم عرض مكتمل قبل الموعد النهائي."),
    "Submission Deadline Reminder": ("Submission Deadline Reminder | تذكير بموعد الإغلاق", "The submission deadline is approaching.", "يقترب الموعد النهائي لتقديم العرض."),
    "Bid Submission Receipt": ("Submission Receipt | إشعار استلام العرض", "Your submission was received and registered successfully.", "تم استلام عرضكم وتسجيله بنجاح."),
    "Supplier Information Request": ("Additional Information Required | مطلوب معلومات إضافية", "Additional supplier information or evidence is required.", "يلزم تقديم معلومات أو أدلة إضافية عن المورد."),
    "Supplier Profile Approved": ("Supplier Profile Approved | اعتماد ملف المورد", "The supplier profile passed the required review.", "اجتاز ملف المورد المراجعة المطلوبة."),
    "Supplier Profile Rejected": ("Supplier Profile Decision | قرار بشأن ملف المورد", "The supplier profile could not be approved in its current form.", "تعذر اعتماد ملف المورد بصورته الحالية."),
    "Award Recommendation Submitted": ("Award Recommendation Submitted | رفع توصية الترسية", "The award recommendation is ready for review.", "توصية الترسية جاهزة للمراجعة."),
    "Award Notification": ("Award Notification | إشعار الترسية", "A procurement award decision has been approved.", "تم اعتماد قرار ترسية المشتريات."),
    "Unsuccessful Bidder Notice": ("Bid Outcome Notice | إشعار بنتيجة العرض", "The submitted offer was not selected for award.", "لم يتم اختيار العرض المقدم للترسية."),
    "Contract Approval Required": ("Contract Approval Required | مطلوب اعتماد العقد", "A procurement contract is awaiting approval.", "يوجد عقد مشتريات بانتظار الاعتماد."),
    "Contract Activated": ("Contract Activated | تفعيل العقد", "The procurement contract is now active.", "أصبح عقد المشتريات فعالا."),
    "Receipt Inspection Required": ("Receipt Inspection Required | مطلوب فحص الاستلام", "A purchase receipt requires inspection before acceptance.", "يتطلب استلام المشتريات فحصا قبل القبول."),
    "Receipt Acceptance Notice": ("Receipt Acceptance Notice | إشعار قبول الاستلام", "The receipt acceptance status has been updated.", "تم تحديث حالة قبول الاستلام."),
    "Stock Handover Notice": ("Stock Handover Notice | إشعار تسليم مخزني", "A stock handover requires acknowledgement.", "يتطلب التسليم المخزني إقرارا بالاستلام."),
    "Handover Discrepancy Notice": ("Handover Discrepancy | فروقات في التسليم", "A stock handover discrepancy requires review.", "توجد فروقات في التسليم المخزني تتطلب المراجعة."),
    "Asset Custody Notice": ("Asset Custody Notice | إشعار عهدة أصل", "An asset custody record requires acknowledgement or action.", "يتطلب سجل عهدة الأصل الإقرار أو اتخاذ إجراء."),
    "Asset Incident Notice": ("Asset Incident Notice | إشعار حادث أصل", "An asset incident has been registered and requires review.", "تم تسجيل حادث أصل ويتطلب المراجعة."),
    "Inspection Due Reminder": ("Inspection Due Reminder | تذكير بالفحص", "A receipt or asset inspection is due.", "حان موعد فحص استلام أو أصل."),
    "Verification Approval Notice": ("Verification Approval Notice | إشعار اعتماد الجرد", "A physical verification is ready for approval.", "الجرد الفعلي جاهز للاعتماد."),
    "Custody Assignment Notice": ("Custody Assignment | إشعار عهدة", "An asset custody record has been assigned.", "تم إسناد سجل عهدة."),
    "Custody Return Reminder": ("Custody Return Reminder | تذكير بإرجاع العهدة", "The expected custody return date is approaching or overdue.", "يقترب موعد إرجاع العهدة أو تجاوز الموعد."),
    "Incident Decision Pending": ("Incident Decision Pending | قرار حادث أصل معلق", "An asset incident requires a decision.", "يتطلب حادث الأصل اتخاذ قرار."),
    "Verification Approval Pending": ("Verification Approval Pending | اعتماد الجرد معلق", "A physical verification requires approval.", "يتطلب الجرد الفعلي الاعتماد."),
}


def upsert_templates():
    body_field = "response" if frappe.get_meta("Email Template").has_field("response") else "response_html"
    for name, (subject, en, ar) in TEMPLATES.items():
        existing = frappe.db.exists("Email Template", name)
        doc = frappe.get_doc("Email Template", name) if existing else frappe.new_doc("Email Template")
        if not existing:
            doc.name = name
        doc.subject = subject + " - {{ doc.name }}"
        doc.use_html = 1
        doc.set(body_field, body(subject.split(" | ")[0], subject.split(" | ")[-1], en, ar))
        doc.save(ignore_permissions=True) if existing else doc.insert(ignore_permissions=True)


def render(template_name, doctype, name):
    frappe.has_permission(doctype, "read", name, throw=True)
    doc = frappe.get_doc(doctype, name)
    template = frappe.get_doc("Email Template", template_name)
    body_field = "response" if template.meta.has_field("response") else "response_html"
    context = {"doc": doc, "record_url": get_url_to_form(doctype, name)}
    return {"subject": render_template(template.subject, context), "message": render_template(template.get(body_field) or "", context)}


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

def _allowed_template(reference_doctype, template_name):
    mapping={
      "Material Request":{"Approved Purchase Request"},
      "Procurement Process":{"Procurement Process Assignment","Award Recommendation Submitted","Award Notification"},
      "Procurement Notice":{"Procurement Invitation","Submission Deadline Reminder"},
      "Procurement Submission":{"Bid Submission Receipt","Unsuccessful Bidder Notice"},
      "Supplier Registration":{"Supplier Information Request","Supplier Profile Approved","Supplier Profile Rejected"},
      "Procurement Contract":{"Contract Approval Required","Contract Activated"},
    }
    if template_name not in mapping.get(reference_doctype,set()):
        frappe.throw(_("Template {0} is not allowed for {1}.").format(template_name,reference_doctype))

@frappe.whitelist()
def preview_template(reference_doctype,reference_name,template_name):
    _allowed_template(reference_doctype,template_name)
    return preview(template_name,reference_doctype,reference_name)

@frappe.whitelist()
def send_template(reference_doctype,reference_name,template_name,recipients,cc=None):
    _allowed_template(reference_doctype,template_name)
    return send(template_name,reference_doctype,reference_name,recipients,cc)
