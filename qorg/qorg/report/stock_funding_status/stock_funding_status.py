import frappe
from frappe import _
def execute(filters=None):
 if not frappe.has_permission('Stock Ledger Entry', "read"):
  frappe.throw(_("Not permitted to view this report."), frappe.PermissionError)
 filters=frappe._dict(filters or {});values={};conditions=['sle.is_cancelled=0']
 mapping={'company':'sle.company','project':'sle.project','warehouse':'sle.warehouse','funding_source':'w.custom_default_funding_source'}
 for key,field in mapping.items():
  if filters.get(key):conditions.append(field+' = %('+key+')s');values[key]=filters[key]
 if filters.get('from_date'):conditions.append('sle.posting_date >= %(from_date)s');values['from_date']=filters.from_date
 if filters.get('to_date'):conditions.append('sle.posting_date <= %(to_date)s');values['to_date']=filters.to_date
 sql='''select sle.item_code item,sle.warehouse,sle.project,w.custom_default_funding_source funding_source,sum(sle.actual_qty) quantity,sum(sle.stock_value_difference) value
 from `tabStock Ledger Entry` sle left join `tabWarehouse` w on w.name=sle.warehouse where '''+' AND '.join(conditions)+''' group by sle.item_code,sle.warehouse,sle.project,w.custom_default_funding_source having abs(sum(sle.actual_qty))>0'''
 data=frappe.db.sql(sql,values,as_dict=True)
 for row in data:row['item__title']=frappe.db.get_value('Item',row.item,'item_name') or row.item
 columns=[{'label':_('Item'),'fieldname':'item','fieldtype':'Link','options':'Item','width':150},{'label':_('Warehouse'),'fieldname':'warehouse','fieldtype':'Link','options':'Warehouse','width':150},{'label':_('Project'),'fieldname':'project','fieldtype':'Link','options':'Project','width':140},{'label':_('Funding Source'),'fieldname':'funding_source','fieldtype':'Link','options':'Project Funding Source','width':150},{'label':_('Quantity'),'fieldname':'quantity','fieldtype':'Float','width':100},{'label':_('Stock Value'),'fieldname':'value','fieldtype':'Currency','width':120}]
 if not set(frappe.get_roles()).intersection({'System Manager','Accounts Manager','Accounts User','Finance Reviewer'}):columns=[c for c in columns if c['fieldname']!='value'];[r.pop('value',None) for r in data]
 summary=[{'label':_('Stock Lines'),'value':len(data),'indicator':'Blue'},{'label':_('Total Quantity'),'value':sum((r.quantity or 0) for r in data),'indicator':'Green'}]
 return columns,data,None,None,summary
