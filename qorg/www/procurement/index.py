import frappe

def get_context(context):
 context.no_cache=1
 context.notices=frappe.get_all('Procurement Notice',filters={'published':1,'docstatus':1},fields=['name','title','notice_type','deadline','route'],order_by='deadline asc')
 return context
