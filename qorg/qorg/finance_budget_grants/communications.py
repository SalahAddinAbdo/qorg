from __future__ import annotations
import frappe
MARKER = "<!-- qorg-finance-template:v1.5.6 -->"
TEMPLATES={
 "Funding Agreement Action Required":("Funding Agreement Action Required | إجراء مطلوب لاتفاقية التمويل","A funding agreement requires action.","تتطلب اتفاقية التمويل اتخاذ إجراء."),
 "Funding Obligation Reminder":("Funding Obligation Reminder | تذكير بالتزام تمويلي","A funding obligation is due or overdue.","حان موعد التزام تمويلي أو أصبح متأخرا."),
 "Financial Control Exception":("Financial Control Exception | استثناء في الرقابة المالية","A financial control exception requires action.","يوجد استثناء في الرقابة المالية يتطلب إجراء."),
}
def _body(en, ar):
    return MARKER + f"""{{% set record = doc if doc is defined else {{}} %}}
<div style='font-family:Arial,sans-serif;line-height:1.6'>
<div dir='ltr'><h3>{en}</h3><ul>
<li>Agreement: {{{{ record.get('agreement_title') or record.get('name') or 'Funding Agreement' }}}}</li>
<li>Project: {{{{ record.get('project') or '-' }}}}</li><li>Donor: {{{{ record.get('donor') or '-' }}}}</li>
<li>Status: {{{{ record.get('status') or '-' }}}}</li><li>Value: {{{{ record.get('agreement_amount') or '-' }}}} {{{{ record.get('agreement_currency') or '' }}}}</li>
{{% if obligation_type is defined %}}<li>Obligation: {{{{ obligation_type }}}} - {{{{ obligation_title|default('-') }}}}</li><li>Due: {{{{ obligation_due_date|default('-') }}}}</li>{{% endif %}}
{{% if exception_code is defined %}}<li>Exception: {{{{ exception_code }}}}</li><li>Reason: {{{{ exception_reason|default('-') }}}}</li>{{% endif %}}
</ul>{{% if record.get('doctype') and record.get('name') %}}<p><a href='{{{{ frappe.utils.get_url_to_form(record.get("doctype"), record.get("name")) }}}}'>Open record</a></p>{{% endif %}}</div>
<hr><div dir='rtl' style='text-align:right'><h3>{ar}</h3><ul>
<li>الاتفاقية: {{{{ record.get('agreement_title') or record.get('name') or 'اتفاقية التمويل' }}}}</li>
<li>المشروع: {{{{ record.get('project') or '-' }}}}</li><li>المانح: {{{{ record.get('donor') or '-' }}}}</li>
<li>الحالة: {{{{ record.get('status') or '-' }}}}</li><li>القيمة: {{{{ record.get('agreement_amount') or '-' }}}} {{{{ record.get('agreement_currency') or '' }}}}</li>
</ul>{{% if record.get('doctype') and record.get('name') %}}<p><a href='{{{{ frappe.utils.get_url_to_form(record.get("doctype"), record.get("name")) }}}}'>فتح السجل</a></p>{{% endif %}}</div></div>"""

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
