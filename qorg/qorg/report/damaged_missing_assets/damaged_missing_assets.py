import frappe
from frappe import _
def execute(filters=None):
 if not frappe.has_permission('Asset Incident', "read"):
  frappe.throw(_("Not permitted to view this report."), frappe.PermissionError)
 filters=frappe._dict(filters or {});values={};conditions=[]
 mapping={'company': 'company', 'project': 'project', 'status': 'incident_status'}
 for key,field in mapping.items():
  if filters.get(key):conditions.append("i."+field+" = %("+key+")s");values[key]=filters[key]
 if filters.get("from_date"):conditions.append("i."+("posting_date" if "posting_date" in "select i.name reference,i.incident_date date,i.asset item,i.responsible_person party,i.project,i.incident_type classification,i.incident_status status,i.estimated_loss value from `tabAsset Incident` i where i.docstatus<2 and i.incident_type in ('Damage','Loss','Theft','Custody Damage','Irreparable Asset')" else "transaction_date" if "transaction_date" in "select i.name reference,i.incident_date date,i.asset item,i.responsible_person party,i.project,i.incident_type classification,i.incident_status status,i.estimated_loss value from `tabAsset Incident` i where i.docstatus<2 and i.incident_type in ('Damage','Loss','Theft','Custody Damage','Irreparable Asset')" else "incident_date" if "incident_date" in "select i.name reference,i.incident_date date,i.asset item,i.responsible_person party,i.project,i.incident_type classification,i.incident_status status,i.estimated_loss value from `tabAsset Incident` i where i.docstatus<2 and i.incident_type in ('Damage','Loss','Theft','Custody Damage','Irreparable Asset')" else "issue_date")+" >= %(from_date)s");values["from_date"]=filters.from_date
 if filters.get("to_date"):conditions.append("i."+("posting_date" if "posting_date" in "select i.name reference,i.incident_date date,i.asset item,i.responsible_person party,i.project,i.incident_type classification,i.incident_status status,i.estimated_loss value from `tabAsset Incident` i where i.docstatus<2 and i.incident_type in ('Damage','Loss','Theft','Custody Damage','Irreparable Asset')" else "transaction_date" if "transaction_date" in "select i.name reference,i.incident_date date,i.asset item,i.responsible_person party,i.project,i.incident_type classification,i.incident_status status,i.estimated_loss value from `tabAsset Incident` i where i.docstatus<2 and i.incident_type in ('Damage','Loss','Theft','Custody Damage','Irreparable Asset')" else "incident_date" if "incident_date" in "select i.name reference,i.incident_date date,i.asset item,i.responsible_person party,i.project,i.incident_type classification,i.incident_status status,i.estimated_loss value from `tabAsset Incident` i where i.docstatus<2 and i.incident_type in ('Damage','Loss','Theft','Custody Damage','Irreparable Asset')" else "issue_date")+" <= %(to_date)s");values["to_date"]=filters.to_date
 base="select i.name reference,i.incident_date date,i.asset item,i.responsible_person party,i.project,i.incident_type classification,i.incident_status status,i.estimated_loss value from `tabAsset Incident` i where i.docstatus<2 and i.incident_type in ('Damage','Loss','Theft','Custody Damage','Irreparable Asset')"
 tail=""
 for marker in (" group by "," having "):
  if marker in base.lower():
   pos=base.lower().find(marker);tail=base[pos:];base=base[:pos];break
 sql=base + (" AND " + " AND ".join(conditions) if conditions else "") + tail
 data=frappe.db.sql(sql,values,as_dict=True)
 for row in data:
  if row.get("item"): row["item__title"]=frappe.db.get_value("Item",row.item,"item_name") or row.item
  row["reference__title"]=row.get("reference")
 columns=[{"label":_("Reference"),"fieldname":"reference","fieldtype":"Link","options":"Asset Incident","width":150},{"label":_("Date"),"fieldname":"date","fieldtype":"Date","width":100},{"label":_("Party or Asset"),"fieldname":"party","width":160},{"label":_("Item"),"fieldname":"item","fieldtype":"Link","options":"Item","width":140},{"label":_("Project"),"fieldname":"project","fieldtype":"Link","options":"Project","width":140},{"label":_("Classification"),"fieldname":"classification","width":150},{"label":_("Quantity"),"fieldname":"quantity","fieldtype":"Float","width":100},{"label":_("Value"),"fieldname":"value","fieldtype":"Currency","width":120},{"label":_("Status"),"fieldname":"status","width":130}]
 present={k for row in data for k in row.keys()};columns=[c for c in columns if c["fieldname"] in present or c["fieldname"] in ("reference","date")]
 if "value" in ('value',) and not set(frappe.get_roles()).intersection({"System Manager","Accounts Manager","Accounts User","Finance Reviewer"}):columns=[c for c in columns if c["fieldname"]!="value"];[r.pop("value",None) for r in data]
 summary=[{"label":_("Records"),"value":len(data),"indicator":"Blue"},{"label":_("Open or Pending"),"value":sum(1 for r in data if any(x in str(r.get("status") or "").lower() for x in ("open","pending","overdue","review"))),"indicator":"Orange"},{"label":_("Total Quantity"),"value":sum((r.get("quantity") or 0) for r in data),"indicator":"Green"}]
 return columns,data,None,None,summary
