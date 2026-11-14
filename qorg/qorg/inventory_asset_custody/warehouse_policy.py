import frappe
from frappe import _
BLOCKED={'Receiving','Quarantine or Inspection','Rejected Stock','Damaged Stock'}
def policy(name):
 fields=[x for x in ('custom_warehouse_role','custom_project_restricted','custom_default_project','custom_funding_restricted','custom_default_funding_source','custom_issue_allowed','custom_receipt_allowed','custom_transfer_allowed') if frappe.get_meta('Warehouse').has_field(x)]
 return frappe.db.get_value('Warehouse',name,fields,as_dict=True) or frappe._dict()
def validate_stock_entry(doc,method=None):
 funding=getattr(doc,'custom_funding_source',None)
 for row in doc.items:
  project=getattr(row,'project',None) or getattr(doc,'project',None)
  for name,source in ((row.s_warehouse,True),(row.t_warehouse,False)):
   if not name:continue
   p=policy(name); role=p.get('custom_warehouse_role')
   quality_release=bool(getattr(doc,'custom_quality_inspection',None) and doc.purpose=='Material Transfer' and role=='Quarantine or Inspection')
   if source and doc.purpose in {'Material Issue','Material Transfer'} and not quality_release and (role in BLOCKED or p.get('custom_issue_allowed')==0):frappe.throw(_('Issue is not allowed from warehouse {0}.').format(name))
   if not source and p.get('custom_receipt_allowed')==0:frappe.throw(_('Receipt is not allowed into warehouse {0}.').format(name))
   if doc.purpose=='Material Transfer' and p.get('custom_transfer_allowed')==0:frappe.throw(_('Transfer is not allowed for warehouse {0}.').format(name))
   if p.get('custom_project_restricted') and project!=p.get('custom_default_project'):frappe.throw(_('Warehouse {0} is restricted to project {1}.').format(name,p.get('custom_default_project')))
   if p.get('custom_funding_restricted') and funding!=p.get('custom_default_funding_source'):frappe.throw(_('Warehouse {0} is restricted to funding source {1}.').format(name,p.get('custom_default_funding_source')))
