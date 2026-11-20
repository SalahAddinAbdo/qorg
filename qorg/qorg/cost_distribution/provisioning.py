from __future__ import annotations
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
TRANSACTIONS={"Material Request":("items","Planned Cost Distribution"),"Supplier Quotation":("items","Planned Cost Distribution"),"Purchase Order":("items","Committed Cost Distribution"),"Purchase Invoice":("items","Final Cost Distribution"),"Expense Claim":("expenses","Cost Distribution"),"Stock Entry":("items","Quantity Distribution")}
SOURCE_CHILDREN=("Material Request Item","Supplier Quotation Item","Purchase Order Item","Purchase Invoice Item","Expense Claim Detail","Stock Entry Detail","Service Allowance Line")
def provision_cost_distribution():
 custom={}
 for dt,(after,label) in TRANSACTIONS.items():
  custom[dt]=[
   {"fieldname":"custom_cost_distribution_section","label":label,"fieldtype":"Section Break","insert_after":after,"collapsible":1,"depends_on":"eval:(doc.custom_cost_distributions||[]).length>0","is_system_generated":1,"module":"QOrg"},
   {"fieldname":"custom_cost_distributions","label":"Cost Distributions","fieldtype":"Table","options":"Cost Distribution Row","insert_after":"custom_cost_distribution_section","is_system_generated":1,"module":"QOrg"},
   {"fieldname":"custom_distribution_control_section","label":"Distribution Control","fieldtype":"Section Break","insert_after":"custom_cost_distributions","collapsible":1,"depends_on":"eval:(doc.custom_cost_distributions||[]).length>0","is_system_generated":1,"module":"QOrg"},
   {"fieldname":"custom_distribution_status","label":"Distribution Status","fieldtype":"Select","options":"Not Required\\nPending\\nAuto Applied\\nTransferred\\nManually Adjusted\\nValidated\\nPosted\\nException\\nReversed","default":"Not Required","insert_after":"custom_distribution_control_section","read_only":1,"is_system_generated":1,"module":"QOrg"},
   {"fieldname":"custom_distribution_hash","label":"Distribution Hash","fieldtype":"Data","insert_after":"custom_distribution_status","hidden":1,"read_only":1,"is_system_generated":1,"module":"QOrg"}]
 for dt in SOURCE_CHILDREN:
  if frappe.db.exists("DocType",dt):custom.setdefault(dt,[]).append({"fieldname":"custom_distribution_source_key","label":"Distribution Source Key","fieldtype":"Data","read_only":1,"hidden":1,"unique":0,"is_system_generated":1,"module":"QOrg"})
 create_custom_fields(custom,update=True);provision_dynamic_dimensions();provision_internal_print_formats()
def provision_dynamic_dimensions():
 if not frappe.db.exists("DocType","Accounting Dimension"):return
 fields=[];meta=frappe.get_meta("Cost Distribution Row",cached=False);insert_after="department"
 for dim in frappe.get_all("Accounting Dimension",filters={"disabled":0},fields=["label","fieldname","document_type"],limit_page_length=0):
  if meta.has_field(dim.fieldname):insert_after=dim.fieldname;continue
  fields.append({"fieldname":dim.fieldname,"label":dim.label,"fieldtype":"Link","options":dim.document_type,"insert_after":insert_after,"is_system_generated":1,"module":"QOrg"});insert_after=dim.fieldname
 if fields:create_custom_fields({"Cost Distribution Row":fields},update=True)
def provision_internal_print_formats():
 html='''<h2>{{ _(doc.doctype) }} - {{ doc.name }}</h2>{% if doc.get("custom_cost_distributions") %}<h3>{{ _("Cost Distribution") }}</h3><table class="table table-bordered table-condensed"><thead><tr><th>{{ _("Source") }}</th><th>{{ _("Project") }}</th><th>{{ _("Cost Center") }}</th><th>{{ _("Budget Line") }}</th><th>{{ _("%") }}</th><th>{{ _("Amount") }}</th></tr></thead><tbody>{% for row in doc.custom_cost_distributions %}<tr><td>{{ row.source_row_idx }}</td><td>{{ row.project }}</td><td>{{ row.cost_center }}</td><td>{{ row.budget_line or "" }}</td><td>{{ row.allocation_percentage }}</td><td>{{ frappe.utils.fmt_money(row.allocated_amount,currency=doc.get("currency")) }}</td></tr>{% endfor %}</tbody></table>{% endif %}'''
 for dt in TRANSACTIONS:
  name=f"{dt} - Internal Cost Distribution"
  values={"doc_type":dt,"module":"QOrg","standard":"Yes","custom_format":1,"print_format_type":"Jinja","html":html}
  if frappe.db.exists("Print Format",name):frappe.db.set_value("Print Format",name,values,update_modified=False)
  else:frappe.get_doc({"doctype":"Print Format","name":name,**values}).insert(ignore_permissions=True)
