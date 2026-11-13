import frappe
from frappe import _
from frappe.utils import flt,getdate
def validate_verification(doc,method=None):
 if doc.snapshot_locked and doc.has_value_changed('cutoff_datetime'):frappe.throw(_('Cut-off cannot change after snapshot lock.'))
 variance=False
 for r in doc.items:
  r.variance_qty=flt(r.counted_qty)-flt(r.book_qty);r.variance_value=r.variance_qty*flt(r.valuation_rate);variance=bool(variance or r.variance_qty or r.variance_type)
  if r.variance_type in {'Damaged','Missing'} and not r.incident:frappe.throw(_('Incident is required for row {0}.').format(r.idx))
 doc.variance_status='Variance Found' if variance else 'No Variance'
@frappe.whitelist()
def load_snapshot(name):
 doc=frappe.get_doc('Physical Verification',name);doc.check_permission('write')
 if doc.snapshot_locked:frappe.throw(_('Snapshot is already locked.'))
 doc.set('items',[])
 if doc.verification_type in {'Stock','Combined'}:
  filters={'warehouse':doc.warehouse} if doc.warehouse else {}
  for b in frappe.get_all('Bin',filters=filters,fields=['item_code','warehouse','actual_qty','valuation_rate']):doc.append('items',{'record_type':'Stock Item','item_code':b.item_code,'book_warehouse':b.warehouse,'book_qty':b.actual_qty,'counted_qty':0,'valuation_rate':b.valuation_rate})
 if doc.verification_type in {'Assets','Custody','Combined'}:
  for a in frappe.get_all('Asset',filters={'company':doc.company,'docstatus':1},fields=['name','location','custodian','gross_purchase_amount']):doc.append('items',{'record_type':'Asset','asset':a.name,'book_location':a.location,'book_custodian':a.custodian,'book_qty':1,'counted_qty':0,'valuation_rate':a.gross_purchase_amount})
 doc.snapshot_locked=1;doc.save();return doc
@frappe.whitelist()
def create_adjustments(name):
 doc=frappe.get_doc('Physical Verification',name);doc.check_permission('write')
 if doc.docstatus!=1:frappe.throw(_('Physical Verification must be submitted.'))
 created=[];stock=[r for r in doc.items if r.record_type=='Stock Item' and r.variance_qty]
 if stock:
  rec=frappe.new_doc('Stock Reconciliation');rec.company=doc.company;rec.posting_date=getdate(doc.cutoff_datetime)
  for r in stock:rec.append('items',{'item_code':r.item_code,'warehouse':r.actual_warehouse or r.book_warehouse,'qty':r.counted_qty,'valuation_rate':r.valuation_rate})
  rec.insert();created.append({'doctype':'Stock Reconciliation','name':rec.name})
 return created
