import frappe
from frappe import _
def execute(filters=None):
 if not frappe.has_permission('Stock Entry', "read"):
  frappe.throw(_("Not permitted to view this report."), frappe.PermissionError)
 filters=frappe._dict(filters or {});values={};conditions=[]
 for key in ('company','project'):
  if filters.get(key):conditions.append(f"x.{key} = %({key})s");values[key]=filters[key]
 if filters.get('from_date'):conditions.append('x.date >= %(from_date)s');values['from_date']=filters.from_date
 if filters.get('to_date'):conditions.append('x.date <= %(to_date)s');values['to_date']=filters.to_date
 where=' WHERE '+' AND '.join(conditions) if conditions else ''
 sql="""select * from (
 select se.name reference,se.posting_date date,se.project,se.purpose classification,se.owner party,'Stock Entry' reference_type,se.company from `tabStock Entry` se where se.docstatus=1
 union all
 select am.name,am.transaction_date,am.custom_project,am.purpose,am.owner,'Asset Movement',am.company from `tabAsset Movement` am where am.docstatus=1
 ) x"""+where
 data=frappe.db.sql(sql,values,as_dict=True)
 columns=[{'label':_('Reference'),'fieldname':'reference','fieldtype':'Dynamic Link','options':'reference_type','width':150},{'label':_('Reference Type'),'fieldname':'reference_type','width':130},{'label':_('Date'),'fieldname':'date','fieldtype':'Date','width':100},{'label':_('Project'),'fieldname':'project','fieldtype':'Link','options':'Project','width':140},{'label':_('Movement Type'),'fieldname':'classification','width':150},{'label':_('Owner'),'fieldname':'party','fieldtype':'Link','options':'User','width':140}]
 summary=[{'label':_('Movements'),'value':len(data),'indicator':'Blue'}]
 return columns,data,None,None,summary
