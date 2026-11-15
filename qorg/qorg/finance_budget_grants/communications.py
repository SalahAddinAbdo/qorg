from __future__ import annotations
import frappe
MARKER = "<!-- qorg-finance-template:v1.5.6 -->"
TEMPLATES={
 "Funding Agreement Action Required":("Funding Agreement Action Required | إجراء مطلوب لاتفاقية التمويل","A funding agreement requires action.","تتطلب اتفاقية التمويل اتخاذ إجراء."),
 "Funding Obligation Reminder":("Funding Obligation Reminder | تذكير بالتزام تمويلي","A funding obligation is due or overdue.","حان موعد التزام تمويلي أو أصبح متأخرا."),
 "Financial Control Exception":("Financial Control Exception | استثناء في الرقابة المالية","A financial control exception requires action.","يوجد استثناء في الرقابة المالية يتطلب إجراء."),
}
def _body(en,ar):
 return MARKER+f"""<div style='font-family:Arial,sans-serif;line-height:1.6'><div dir='ltr'><h3>{en}</h3><ul><li>Agreement: {{{{ doc.agreement_title or doc.name }}}}</li><li>Project: {{{{ doc.project or '-' }}}}</li><li>Donor: {{{{ doc.donor or '-' }}}}</li><li>Status: {{{{ doc.status }}}}</li><li>Value: {{{{ doc.agreement_amount }}}} {{{{ doc.agreement_currency }}}}</li>{{% if obligation_type %}}<li>Obligation: {{{{ obligation_type }}}} - {{{{ obligation_title or '-' }}}}</li><li>Due: {{{{ obligation_due_date }}}}; overdue days: {{{{ days_overdue or 0 }}}}</li>{{% endif %}}{{% if exception_code %}}<li>Exception: {{{{ exception_code }}}}</li><li>Reason: {{{{ exception_reason or '-' }}}}</li>{{% endif %}}</ul><p><a href='{{{{ frappe.utils.get_url_to_form(doc.doctype, doc.name) }}}}'>Open record</a></p></div><hr><div dir='rtl' style='text-align:right'><h3>{ar}</h3><ul><li>الاتفاقية: {{{{ doc.agreement_title or doc.name }}}}</li><li>المشروع: {{{{ doc.project or '-' }}}}</li><li>المانح: {{{{ doc.donor or '-' }}}}</li><li>الحالة: {{{{ doc.status }}}}</li><li>القيمة: {{{{ doc.agreement_amount }}}} {{{{ doc.agreement_currency }}}}</li>{{% if obligation_type %}}<li>الالتزام: {{{{ obligation_type }}}} - {{{{ obligation_title or '-' }}}}</li><li>الاستحقاق: {{{{ obligation_due_date }}}}؛ أيام التأخير: {{{{ days_overdue or 0 }}}}</li>{{% endif %}}{{% if exception_code %}}<li>الاستثناء: {{{{ exception_code }}}}</li><li>السبب: {{{{ exception_reason or '-' }}}}</li>{{% endif %}}</ul><p><a href='{{{{ frappe.utils.get_url_to_form(doc.doctype, doc.name) }}}}'>فتح السجل</a></p></div></div>"""
def provision_templates():
 result={"created":[],"updated":[],"adopted":[],"skipped_manual":[]}; meta=frappe.get_meta("Email Template")
 for name,(subject,en,ar) in TEMPLATES.items():
  exists=frappe.db.exists("Email Template",name); doc=frappe.get_doc("Email Template",name) if exists else frappe.new_doc("Email Template"); managed=_body(en,ar); previous=doc.get("response") or doc.get("response_html") or ""
  if not exists:
   doc.name=name; action="created"
  elif not previous:
   action="adopted"
  elif "qorg-finance-template:" in previous:
   action="updated"
  else:
   result["skipped_manual"].append(name); continue
  doc.subject=subject; doc.use_html=1; doc.response=managed
  if meta.has_field("response_html"): doc.response_html=managed
  doc.save(ignore_permissions=True) if exists else doc.insert(ignore_permissions=True)
  result[action].append(name)
 return result
