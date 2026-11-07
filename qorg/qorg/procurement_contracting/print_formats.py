import frappe
FORMATS={
 "Q Universal - Procurement Bid Opening Minutes":"Procurement Bid Opening",
 "Q Universal - Technical Evaluation":"Technical Evaluation",
 "Q Universal - Financial Evaluation":"Financial Evaluation",
 "Q Universal - Award Decision":"Award Decision",
 "Q Universal - Procurement Contract":"Procurement Contract",
 "Q Universal - Procurement Acceptance":"Procure Acceptance",
}
FALLBACK="""<div class='qorg-print'><h2>{{ _(doc.doctype) }}</h2><p><b>{{ _('Reference') }}:</b> {{ doc.name }} &nbsp; <b>{{ _('Status') }}:</b> {{ doc.workflow_state or doc.status or '' }}</p><hr>{% for field in doc.meta.fields %}{% set value=doc.get(field.fieldname) %}{% if field.fieldtype == 'Table' and value %}<h4>{{ _(field.label) }}</h4><table class='table table-bordered table-condensed'>{% for row in value %}<tr>{% for df in frappe.get_meta(field.options).fields %}{% if df.in_list_view and df.fieldname != 'page_break' %}<td><b>{{ _(df.label) }}:</b> {{ frappe.format_value(row.get(df.fieldname), df, row) }}</td>{% endif %}{% endfor %}</tr>{% if row.page_break %}</table><div style='page-break-after:always'></div><table class='table table-bordered table-condensed'>{% endif %}{% endfor %}</table>{% elif field.fieldtype not in ['Section Break','Column Break','Tab Break','HTML','Button','Table'] and value not in [None,''] %}<div><b>{{ _(field.label) }}:</b> {{ frappe.format_value(value, field, doc) }}</div>{% endif %}{% endfor %}</div>"""

def _managed_html():
 for name in frappe.get_all("Print Format",filters={"name":["like","Q Universal%"]},pluck="name",limit=1):
  return frappe.db.get_value("Print Format",name,"html") or FALLBACK
 return FALLBACK
def provision_print_formats():
 html=_managed_html()
 for name,doctype in FORMATS.items():
  if frappe.db.exists("Print Format",name): continue
  frappe.get_doc({"doctype":"Print Format","name":name,"doc_type":doctype,"print_format_type":"Jinja","html":html,"custom_format":1,"disabled":0}).insert(ignore_permissions=True)
