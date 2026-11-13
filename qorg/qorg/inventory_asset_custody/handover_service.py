import frappe
from frappe import _
from frappe.utils import flt
def populate_from_stock_entry(doc):
 if not doc.stock_entry or doc.items:return
 se=frappe.get_doc('Stock Entry',doc.stock_entry)
 if se.docstatus!=1:frappe.throw(_('Stock Entry must be submitted.'))
 doc.company=se.company;doc.material_request=getattr(se,'custom_material_request',None);doc.project=getattr(se,'project',None);doc.funding_source=getattr(se,'custom_funding_source',None);doc.activity_reference=getattr(se,'custom_activity_reference',None);doc.handed_over_by=frappe.session.user
 for r in se.items:
  doc.append('items',{'stock_entry_detail':r.name,'item_code':r.item_code,'item_name':r.item_name,'uom':r.uom,'issued_qty':r.qty,'delivered_qty':r.qty,'received_qty':r.qty,'batch_no':getattr(r,'batch_no',None),'serial_numbers':getattr(r,'serial_no',None)})
def validate_handover(doc):
 duplicate=frappe.db.exists('Stock Handover',{'stock_entry':doc.stock_entry,'name':['!=',doc.name or ''],'docstatus':['<',2]})
 if duplicate:frappe.throw(_('Stock Entry already has handover {0}.').format(duplicate))
 difference=False
 for r in doc.items:
  if min(flt(r.delivered_qty),flt(r.received_qty),flt(r.rejected_qty),flt(r.damaged_qty))<0:frappe.throw(_('Quantities cannot be negative.'))
  if flt(r.delivered_qty)>flt(r.issued_qty) or flt(r.received_qty)>flt(r.delivered_qty):frappe.throw(_('Invalid quantities in row {0}.').format(r.idx))
  r.short_qty=max(flt(r.delivered_qty)-flt(r.received_qty),0);difference=bool(difference or r.short_qty or r.rejected_qty or r.damaged_qty)
 doc.discrepancy_status='Open' if difference else 'None';doc.fully_acknowledged=0 if difference else 1;doc.handover_status='Discrepancy Review' if difference else 'Pending Handover'
