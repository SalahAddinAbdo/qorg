import frappe
from frappe import _
from frappe.utils.jinja import render_template

TEMPLATES = {
 "Procurement Invitation": {"subject":"Invitation to Participate | دعوة للمشاركة - {{ doc.name }}","body":"""<div dir='auto'><p>Dear Supplier,</p><p>You are invited to participate in <b>{{ doc.title or doc.name }}</b>. Please review the published documents and submit before {{ doc.deadline or '' }}.</p><hr><p dir='rtl'>السادة الموردون،</p><p dir='rtl'>ندعوكم للمشاركة في <b>{{ doc.title or doc.name }}</b>. يرجى مراجعة وثائق المنافسة والتقديم قبل {{ doc.deadline or '' }}.</p><p><a href='{{ frappe.utils.get_url_to_form(doc.doctype, doc.name) }}'>Open record | فتح السجل</a></p></div>"""},
 "Bid Submission Receipt": {"subject":"Submission Receipt | إشعار استلام العرض - {{ doc.name }}","body":"""<div dir='auto'><p>Your submission was received successfully for {{ doc.procurement_process }}.</p><p dir='rtl'>تم استلام عرضكم بنجاح للمنافسة {{ doc.procurement_process }}.</p><p><b>Reference | المرجع:</b> {{ doc.name }}</p></div>"""},
 "Award Notification": {"subject":"Award Decision | قرار الترسية - {{ doc.name }}","body":"""<div dir='auto'><p>The procurement award decision for {{ doc.procurement_process or doc.name }} is now available.</p><p dir='rtl'>أصبح قرار ترسية المنافسة {{ doc.procurement_process or doc.name }} متاحا.</p><p><a href='{{ frappe.utils.get_url_to_form(doc.doctype, doc.name) }}'>Open decision | فتح القرار</a></p></div>"""},
 "Unsuccessful Bidder Notice": {"subject":"Procurement Result | نتيجة المنافسة - {{ doc.name }}","body":"""<div dir='auto'><p>Thank you for participating. Your submission was not selected in this procurement. This notice does not disclose confidential evaluation information.</p><p dir='rtl'>شكرا لمشاركتكم. لم يتم اختيار عرضكم في هذه المنافسة. لا يتضمن هذا الإشعار معلومات تقييم سرية.</p></div>"""},
 "Contract Approval": {"subject":"Contract Approval Required | مطلوب اعتماد العقد - {{ doc.name }}","body":"""<div dir='auto'><p>Contract {{ doc.name }} requires review and approval.</p><p dir='rtl'>يتطلب العقد {{ doc.name }} المراجعة والاعتماد.</p><p><a href='{{ frappe.utils.get_url_to_form(doc.doctype, doc.name) }}'>Open contract | فتح العقد</a></p></div>"""},
}

def provision_email_templates():
 for name,spec in TEMPLATES.items():
  if not frappe.db.exists('Email Template',name): frappe.get_doc({'doctype':'Email Template','name':name,'subject':spec['subject'],'response':spec['body'],'use_html':1}).insert(ignore_permissions=True)

@frappe.whitelist()
def preview_template(reference_doctype, reference_name, template_name):
 frappe.has_permission(reference_doctype,'read',reference_name,throw=True)
 doc=frappe.get_doc(reference_doctype,reference_name); template=frappe.get_doc('Email Template',template_name)
 return {'subject':render_template(template.subject or '',{'doc':doc}), 'message':render_template(template.response or '',{'doc':doc})}

@frappe.whitelist()
def send_template(reference_doctype, reference_name, template_name, recipients, cc=None):
 frappe.has_permission(reference_doctype,'read',reference_name,throw=True)
 if isinstance(recipients,str): recipients=[x.strip() for x in recipients.replace(';',',').split(',') if x.strip()]
 if not recipients: frappe.throw(_('At least one recipient is required.'))
 preview=preview_template(reference_doctype,reference_name,template_name)
 frappe.sendmail(recipients=recipients,cc=cc or None,subject=preview['subject'],message=preview['message'],reference_doctype=reference_doctype,reference_name=reference_name)
 return {'sent':True,'recipients':recipients}
