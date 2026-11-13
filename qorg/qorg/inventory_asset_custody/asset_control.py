import frappe
from frappe import _
BLOCKED={'Sold','Scrapped','Cancelled','Disposed'}
def validate_custody(doc):
 asset=frappe.get_doc('Asset',doc.asset)
 if asset.status in BLOCKED:frappe.throw(_('Asset cannot be assigned while status is {0}.').format(asset.status))
 repair=frappe.db.exists('Asset Repair',{'asset':doc.asset,'docstatus':['<',2],'repair_status':['not in',['Completed','Cancelled']]})
 if repair:frappe.throw(_('Asset is under repair {0}.').format(repair))
 active=frappe.db.exists('Asset Custody',{'asset':doc.asset,'name':['!=',doc.name or ''],'docstatus':['<',2],'custody_status':['in',['Pending Handover','Active','Return Due','Overdue']]})
 if active:frappe.throw(_('Asset already has active custody {0}.').format(active))
def sync_asset_custody(doc,active):
 values={'custom_current_custody':doc.name if active else None,'custom_custody_status':'Active' if active else 'Returned'}
 frappe.db.set_value('Asset',doc.asset,values,update_modified=False)
def validate_asset(doc,method=None):
 if doc.status in BLOCKED and getattr(doc,'custom_disposal_approval_required',0) and not getattr(doc,'custom_disposal_approval_reference',None):frappe.throw(_('Disposal approval reference is required.'))
def validate_movement(doc,method=None):
 for r in doc.assets:
  asset=frappe.get_doc('Asset',r.asset)
  if asset.status in BLOCKED:frappe.throw(_('Asset {0} cannot be moved.').format(r.asset))
  if frappe.db.exists('Asset Repair',{'asset':r.asset,'docstatus':['<',2],'repair_status':['not in',['Completed','Cancelled']]}):frappe.throw(_('Asset {0} is under repair.').format(r.asset))
def prevent_separation(doc,method=None):
 if not getattr(doc,'employee',None):return
 active=frappe.db.exists('Asset Custody',{'custodian':doc.employee,'docstatus':['<',2],'custody_status':['in',['Pending Handover','Active','Return Due','Overdue']]})
 if active and not getattr(doc,'custom_custody_exception_approved',0):frappe.throw(_('Employee has active custody {0}.').format(active))
