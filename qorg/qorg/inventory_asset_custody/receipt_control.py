from __future__ import annotations
import frappe
from frappe import _
from frappe.utils import flt,getdate
CLOSED={'Closed','Cancelled','Expired','Terminated'}
def reconcile_receipt(doc,method=None):
 settings=frappe.get_cached_doc('Stock Settings'); tolerance=flt(settings.custom_over_receipt_tolerance) if getattr(settings,'custom_allow_over_receipt',0) else 0
 contract=getattr(doc,'custom_procurement_contract',None)
 if contract:
  fields=[x for x in ('company','status','end_date','extended_end_date') if frappe.get_meta('Procurement Contract').has_field(x)]
  c=frappe.db.get_value('Procurement Contract',contract,fields,as_dict=True) or {}
  if c.get('company') and c.company!=doc.company:frappe.throw(_('Contract company must match receipt company.'))
  if c.get('status') in CLOSED:frappe.throw(_('Receipt is not allowed against contract {0} with status {1}.').format(contract,c.status))
  expiry=c.get('extended_end_date') or c.get('end_date')
  if expiry and getdate(doc.posting_date)>getdate(expiry):frappe.throw(_('Contract {0} expired on {1}.').format(contract,expiry))
 accepted_total=rejected_total=0
 for row in doc.items:
  ordered=flt(frappe.db.get_value('Purchase Order Item',row.purchase_order_item,'qty')) if row.purchase_order_item else 0
  prior=frappe.db.sql('''select coalesce(sum(case when pr.is_return=0 then abs(pri.qty) else -abs(pri.qty) end),0) received,coalesce(sum(case when pr.is_return=0 then pri.custom_accepted_qty else -abs(pri.qty) end),0) accepted,coalesce(sum(case when pr.is_return=0 then pri.rejected_qty else 0 end),0) rejected from `tabPurchase Receipt Item` pri join `tabPurchase Receipt` pr on pr.name=pri.parent where pr.docstatus=1 and pri.purchase_order_item=%s and pr.name!=%s''',(row.purchase_order_item,doc.name or ''),as_dict=True)[0] if row.purchase_order_item else frappe._dict(received=0,accepted=0,rejected=0)
  current=abs(flt(row.qty)); accepted=flt(row.custom_accepted_qty); rejected=flt(row.rejected_qty)
  if ordered and flt(prior.received)+current>ordered*(1+tolerance/100)+0.000001:frappe.throw(_('Row {0} exceeds the allowed Purchase Order quantity.').format(row.idx))
  if accepted+rejected>current+0.000001:frappe.throw(_('Accepted and rejected quantities exceed received quantity in row {0}.').format(row.idx))
  if doc.custom_receipt_inspection_required and accepted and not row.quality_inspection:frappe.throw(_('Quality Inspection is required before acceptance in row {0}.').format(row.idx))
  row.custom_contracted_qty=ordered;row.custom_previously_received_qty=prior.received;row.custom_accepted_qty=accepted;row.custom_returned_qty=max(-flt(prior.received),0);row.custom_replacement_pending_qty=max(flt(prior.rejected)+rejected,0);row.custom_remaining_contract_qty=max(ordered-(flt(prior.accepted)+accepted),0)
  accepted_total+=accepted;rejected_total+=rejected
 if doc.custom_is_final_receipt and any(flt(r.custom_remaining_contract_qty) or flt(r.custom_replacement_pending_qty) for r in doc.items):frappe.throw(_('Final Receipt cannot be completed with remaining or replacement quantities.'))
 doc.custom_receipt_acceptance_status='Partially Accepted' if accepted_total and rejected_total else 'Rejected' if rejected_total else 'Accepted' if accepted_total else 'Pending Inspection'
