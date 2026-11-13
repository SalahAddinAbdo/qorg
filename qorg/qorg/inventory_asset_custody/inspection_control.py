import frappe
from frappe import _
from frappe.utils import flt
ACTIONS={'Accepted':'Release to Accepted Stock','Accepted with Minor Observations':'Release to Accepted Stock','Partially Accepted':'Hold in Quarantine','Rejected':'Move to Rejected Stock','Replacement Required':'Replacement Required','Reinspection Required':'Reinspection Required'}
def validate_inspection(doc,method=None):
 inspected=flt(doc.custom_inspected_qty);accepted=flt(doc.custom_accepted_qty);rejected=flt(doc.custom_rejected_qty);result=doc.custom_qorg_result
 if accepted+rejected>inspected+0.000001:frappe.throw(_('Accepted and rejected quantities exceed inspected quantity.'))
 if result in {'Rejected','Partially Accepted','Replacement Required'} and not rejected:frappe.throw(_('Rejected Quantity is required.'))
 doc.custom_release_action=ACTIONS.get(result,'Hold in Quarantine')
