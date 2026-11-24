from __future__ import annotations
import frappe
from frappe import _
from frappe.utils import get_url_to_form
from frappe.utils.jinja import render_template

VERSION='QORG-LEARNING-COMM-v1.0'; PRIMARY='#176B87'; ACCENT='#D7A83E'
TEMPLATES={
 'QOrg Training Action':('Training Follow-up','Training Action Required | إجراء تدريبي مطلوب','Action required for {{ doc.employee_name or doc.employee }}','Please review the training follow-up and complete the required action by {{ doc.due_date or "-" }}.','يرجى مراجعة متابعة التدريب واستكمال الإجراء المطلوب قبل {{ doc.due_date or "-" }}.'),
 'QOrg Training Result':('Training Result','Training Result | نتيجة التدريب','Training result is available','The training result is available. Open the record to review scores, completion and certificate eligibility.','نتيجة التدريب متاحة. افتح السجل لمراجعة الدرجات والاكتمال وأهلية الشهادة.'),
 'QOrg Evaluation Assignment':('Evaluation Assignment','Evaluation Assignment | تكليف تقييم','Evaluation assignment for {{ doc.employee_name or doc.employee }}','You have been assigned an evaluation. Please complete it by {{ doc.due_date or "-" }}.','تم تكليفك بإجراء تقييم. يرجى استكماله قبل {{ doc.due_date or "-" }}.'),
 'QOrg Appraisal Result':('Appraisal','Appraisal Result | نتيجة تقييم الأداء','Appraisal result for {{ doc.employee_name or doc.employee }}','The appraisal has been finalized. Review the rating, outcome and any development actions.','تم اعتماد تقييم الأداء. راجع التقدير والنتيجة وإجراءات التطوير.'),
}

def _html(title_en,body_en,body_ar):
 return f'''<div style="font-family:Arial,sans-serif;background:#f4f7f8;padding:22px"><div style="max-width:680px;margin:auto;background:#fff;border:1px solid #dfe3e8;border-radius:8px;overflow:hidden"><div style="background:{PRIMARY};color:#fff;padding:18px 22px"><div style="font-size:18px;font-weight:700">{{{{ title }}}}</div></div><div style="padding:22px"><div style="direction:rtl;text-align:right;line-height:1.9">{body_ar}</div><div style="height:1px;background:#e6eaed;margin:18px 0"></div><div style="direction:ltr;text-align:left;line-height:1.7">{body_en}</div><div style="text-align:center;margin-top:24px"><a href="{{{{ record_url }}}}" style="display:inline-block;background:{PRIMARY};color:#fff;text-decoration:none;padding:11px 22px;border-radius:5px;font-weight:700">عرض السجل | View Record</a></div></div><div style="background:#f6f8fa;border-top:1px solid #dfe3e8;padding:11px;text-align:center;color:#697780;font-size:11px">{VERSION}</div></div></div>'''

def provision_communications():
 if not frappe.db.exists('DocType','Email Template'):return
 for name,(dt,subject,title,en,ar) in TEMPLATES.items():
  values={'subject':subject,'response':_html(title,en,ar),'use_html':1,'reference_doctype':dt}
  if frappe.db.exists('Email Template',name):frappe.db.set_value('Email Template',name,values,update_modified=False)
  else:
   doc=frappe.get_doc({'doctype':'Email Template','name':name,**values});doc.insert(ignore_permissions=True)
 _provision_notifications()

def _provision_notifications():
 if not frappe.db.exists('DocType','Notification'):return
 specs=[
  ('QOrg Training Follow-up Due','Training Follow-up','doc.status in ["Open", "In Progress", "Overdue"]','status','QOrg Training Action','responsible_user'),
  ('QOrg Evaluation Assignment Due','Evaluation Assignment','doc.status in ["Assigned", "In Progress"]','status','QOrg Evaluation Assignment','reviewer_user'),
  ('QOrg Appraisal Finalized','Appraisal','doc.qorg_stage == "Finalized"','qorg_stage','QOrg Appraisal Result',''),
 ]
 for name,dt,condition,value_field,template,recipient_field in specs:
  subject=TEMPLATES[template][1]
  message=_html(TEMPLATES[template][2],TEMPLATES[template][3],TEMPLATES[template][4]).replace('{{ record_url }}','{{ frappe.utils.get_url_to_form(doc.doctype, doc.name) }}').replace('{{ title }}',TEMPLATES[template][2])
  values={'subject':subject,'document_type':dt,'event':'Value Change','value_changed':value_field,'condition':condition,'channel':'Email','enabled':1,'message_type':'HTML','message':message,'set_property_after_alert':0}
  if frappe.db.exists('Notification',name):
   doc=frappe.get_doc('Notification',name);doc.update(values);doc.set('recipients',[])
  else:
   doc=frappe.new_doc('Notification');doc.name=name;doc.update(values)
  if recipient_field:doc.append('recipients',{'receiver_by_document_field':recipient_field})
  else:doc.append('recipients',{'receiver_by_role':'HR Manager'})
  doc.save(ignore_permissions=True)

def render(template_name,doctype,name):
 _allowed(template_name,doctype);frappe.has_permission(doctype,'read',name,throw=True);doc=frappe.get_doc(doctype,name);t=frappe.get_doc('Email Template',template_name);ctx={'doc':doc,'record_url':get_url_to_form(doctype,name),'title':TEMPLATES[template_name][2]};return {'subject':render_template(t.subject,ctx),'message':render_template(t.response or '',ctx),'recipients':', '.join(_default_recipients(doctype,doc))}


def _default_recipients(doctype,doc):
 values=[]
 if doctype=='Training Follow-up':values=[doc.responsible_user]
 elif doctype=='Evaluation Assignment':values=[doc.reviewer_user]
 elif doctype=='Appraisal':
  values=[frappe.db.get_value('Employee',doc.employee,'user_id')]
 elif doctype=='Training Result':
  event=frappe.get_doc('Training Event',doc.training_event)
  for row in event.employees:
   user=frappe.db.get_value('Employee',row.employee,'user_id');values.append(user)
 return list(dict.fromkeys(x for x in values if x))

def _allowed(name,dt):
 if name not in TEMPLATES or TEMPLATES[name][0]!=dt:frappe.throw(_('Template is not allowed for this document.'))

@frappe.whitelist()
def preview(template_name,doctype,name):return render(template_name,doctype,name)

@frappe.whitelist()
def send(template_name,doctype,name,recipients,cc=None):
 result=render(template_name,doctype,name);to=[x.strip() for x in (recipients or '').replace(';',',').split(',') if x.strip()]
 if not to:frappe.throw(_('At least one recipient is required.'))
 frappe.sendmail(recipients=to,cc=cc,subject=result['subject'],message=result['message'],reference_doctype=doctype,reference_name=name,delayed=True);return {'sent':True}
