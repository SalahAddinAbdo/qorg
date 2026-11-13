import frappe
from frappe import _
def _email(template,recipient,reference_doctype,reference_name,context):
 if not recipient:frappe.throw(_('Recipient email is required.'))
 t=frappe.get_doc('Email Template',template);context.update({'name':reference_name,'record_url':frappe.utils.get_url_to_form(reference_doctype,reference_name)})
 frappe.sendmail(recipients=[recipient],subject=frappe.render_template(t.subject,context),message=frappe.render_template(t.response_html,context),reference_doctype=reference_doctype,reference_name=reference_name)
@frappe.whitelist()
def make_stock_handover(stock_entry):
 
 if not frappe.has_permission('Stock Handover','create'):
  frappe.throw(_('Not permitted to create Stock Handover.'),frappe.PermissionError)
 se=frappe.get_doc('Stock Entry',stock_entry);se.check_permission('read')
 if se.docstatus!=1:frappe.throw(_('Stock Entry must be submitted.'))
 doc=frappe.new_doc('Stock Handover');doc.stock_entry=se.name;doc.run_method('before_validate');return doc
@frappe.whitelist()
def make_asset_custody(asset_movement):
 
 if not frappe.has_permission('Asset Custody','create'):
  frappe.throw(_('Not permitted to create Asset Custody.'),frappe.PermissionError)
 am=frappe.get_doc('Asset Movement',asset_movement);am.check_permission('read')
 if am.docstatus!=1:frappe.throw(_('Asset Movement must be submitted.'))
 if len(am.assets)!=1:frappe.throw(_('Create one Asset Custody for each asset movement row.'))
 r=am.assets[0];doc=frappe.new_doc('Asset Custody');doc.company=am.company;doc.asset_movement=am.name;doc.asset=r.asset;doc.custody_type='Employee Custody';doc.custodian=getattr(r,'to_employee',None);doc.location=getattr(r,'target_location',None);doc.issue_date=am.transaction_date;return doc
@frappe.whitelist()
def make_asset_return(name):
 c=frappe.get_doc('Asset Custody',name);c.check_permission('read');doc=frappe.new_doc('Asset Movement');doc.company=c.company;doc.purpose='Receipt';doc.custom_asset_custody=c.name;doc.custom_return_against_movement=c.asset_movement;doc.append('assets',{'asset':c.asset,'source_location':c.location,'from_employee':c.custodian});return doc
@frappe.whitelist()
def make_incident(source_doctype,source_name):
 
 if not frappe.has_permission('Asset Incident','create'):
  frappe.throw(_('Not permitted to create Asset Incident.'),frappe.PermissionError)
 src=frappe.get_doc(source_doctype,source_name);src.check_permission('read');doc=frappe.new_doc('Asset Incident');doc.company=src.company;doc.project=getattr(src,'project',None)
 if source_doctype=='Stock Handover':doc.stock_handover=src.name;doc.stock_entry=src.stock_entry;doc.incident_type='Transit Shortage'
 if source_doctype=='Asset Custody':doc.asset_custody=src.name;doc.asset=src.asset;doc.responsible_person=src.custodian;doc.incident_type='Custody Damage'
 return doc
@frappe.whitelist()
def make_asset_repair(name):
 
 if not frappe.has_permission('Asset Repair','create'):
  frappe.throw(_('Not permitted to create Asset Repair.'),frappe.PermissionError)
 inc=frappe.get_doc('Asset Incident',name);inc.check_permission('read');doc=frappe.new_doc('Asset Repair');doc.asset=inc.asset;return doc
@frappe.whitelist()
def send_handover_email(name):
 d=frappe.get_doc('Stock Handover',name);d.check_permission('email');recipient=d.external_recipient_email or frappe.db.get_value('User',d.recipient_user,'email') or frappe.db.get_value('Employee',d.recipient_employee,'company_email');_email('Stock Handover Notice',recipient,d.doctype,d.name,d.as_dict())
@frappe.whitelist()
def send_custody_email(name):
 d=frappe.get_doc('Asset Custody',name);d.check_permission('email');recipient=frappe.db.get_value('Employee',d.custodian,'company_email') or frappe.db.get_value('Employee',d.custodian,'personal_email');_email('Asset Custody Notice',recipient,d.doctype,d.name,d.as_dict())
@frappe.whitelist()
def send_incident_email(name):
 d=frappe.get_doc('Asset Incident',name);d.check_permission('email');recipient=frappe.db.get_value('Employee',d.responsible_person,'company_email');_email('Asset Incident Notice',recipient,d.doctype,d.name,d.as_dict())
