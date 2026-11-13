import frappe
from frappe import _
from frappe.utils import flt
APPROVED={'Approved','Partially Issued','Fully Issued'}
def issued(mri,current=''):
 return flt(frappe.db.sql('''select coalesce(sum(sed.qty),0) from `tabStock Entry Detail` sed join `tabStock Entry` se on se.name=sed.parent where sed.material_request_item=%s and se.docstatus=1 and se.name!=%s''',(mri,current))[0][0])
def validate_stock_entry(doc,method=None):
 mr=doc.custom_material_request
 if doc.purpose=='Material Issue' and mr:
  state=frappe.db.get_value('Material Request',mr,'workflow_state') or frappe.db.get_value('Material Request',mr,'status')
  if state not in APPROVED:frappe.throw(_('Material Request {0} must be approved before issue.').format(mr))
 for row in doc.items:
  if row.material_request_item:
   allowed=flt(frappe.db.get_value('Material Request Item',row.material_request_item,'qty'))
   if issued(row.material_request_item,doc.name or '')+flt(row.qty)>allowed+0.000001:frappe.throw(_('Row {0} exceeds approved Material Request quantity.').format(row.idx))
  if doc.custom_return_against_stock_entry:
   original=flt(frappe.db.get_value('Stock Entry Detail',{'parent':doc.custom_return_against_stock_entry,'item_code':row.item_code},'qty'))
   prior=flt(frappe.db.sql('''select coalesce(sum(abs(sed.qty)),0) from `tabStock Entry Detail` sed join `tabStock Entry` se on se.name=sed.parent where se.docstatus=1 and se.custom_return_against_stock_entry=%s and se.name!=%s and sed.item_code=%s''',(doc.custom_return_against_stock_entry,doc.name or '',row.item_code))[0][0])
   if prior+abs(flt(row.qty))>original+0.000001:frappe.throw(_('Return quantity exceeds original issue for {0}.').format(row.item_code))
def update_material_request(doc,method=None):
 names={doc.custom_material_request} if doc.custom_material_request else set()
 for row in doc.items:
  if row.material_request:names.add(row.material_request)
 for mr in names:
  rows=frappe.get_all('Material Request Item',filters={'parent':mr},fields=['name','qty']);vals=[issued(r.name) for r in rows];status='Fully Issued' if rows and all(vals[i]>=flt(rows[i].qty)-0.000001 for i in range(len(rows))) else 'Partially Issued' if any(vals) else 'Not Issued'
  frappe.db.set_value('Material Request',mr,'custom_issue_status',status,update_modified=False)
