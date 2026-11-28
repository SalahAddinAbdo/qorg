import frappe
def get_context(context):
 settings=frappe.get_single('Accountability Settings');context.no_cache=1;context.enabled=bool(settings.enable_public_tracking);return context
