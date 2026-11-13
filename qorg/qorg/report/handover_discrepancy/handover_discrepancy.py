import frappe
from frappe import _
def execute(filters=None):
 if not frappe.has_permission('Stock Handover', "read"):
  frappe.throw(_("Not permitted to view this report."), frappe.PermissionError)
 filters=frappe._dict(filters or {});values={};conditions=[]
 mapping={'company': 'company', 'project': 'project', 'status': 'discrepancy_status'}
 for key,field in mapping.items():
  if filters.get(key):conditions.append("h."+field+" = %("+key+")s");values[key]=filters[key]
 if filters.get("from_date"):conditions.append("h."+("posting_date" if "posting_date" in "select h.name reference,h.posting_date date,h.project,hi.item_code item,hi.short_qty quantity,hi.discrepancy_type classification,h.discrepancy_status status from `tabStock Handover` h join `tabStock Handover Item` hi on hi.parent=h.name where h.docstatus<2 and h.discrepancy_status!='None'" else "transaction_date" if "transaction_date" in "select h.name reference,h.posting_date date,h.project,hi.item_code item,hi.short_qty quantity,hi.discrepancy_type classification,h.discrepancy_status status from `tabStock Handover` h join `tabStock Handover Item` hi on hi.parent=h.name where h.docstatus<2 and h.discrepancy_status!='None'" else "incident_date" if "incident_date" in "select h.name reference,h.posting_date date,h.project,hi.item_code item,hi.short_qty quantity,hi.discrepancy_type classification,h.discrepancy_status status from `tabStock Handover` h join `tabStock Handover Item` hi on hi.parent=h.name where h.docstatus<2 and h.discrepancy_status!='None'" else "issue_date")+" >= %(from_date)s");values["from_date"]=filters.from_date
 if filters.get("to_date"):conditions.append("h."+("posting_date" if "posting_date" in "select h.name reference,h.posting_date date,h.project,hi.item_code item,hi.short_qty quantity,hi.discrepancy_type classification,h.discrepancy_status status from `tabStock Handover` h join `tabStock Handover Item` hi on hi.parent=h.name where h.docstatus<2 and h.discrepancy_status!='None'" else "transaction_date" if "transaction_date" in "select h.name reference,h.posting_date date,h.project,hi.item_code item,hi.short_qty quantity,hi.discrepancy_type classification,h.discrepancy_status status from `tabStock Handover` h join `tabStock Handover Item` hi on hi.parent=h.name where h.docstatus<2 and h.discrepancy_status!='None'" else "incident_date" if "incident_date" in "select h.name reference,h.posting_date date,h.project,hi.item_code item,hi.short_qty quantity,hi.discrepancy_type classification,h.discrepancy_status status from `tabStock Handover` h join `tabStock Handover Item` hi on hi.parent=h.name where h.docstatus<2 and h.discrepancy_status!='None'" else "issue_date")+" <= %(to_date)s");values["to_date"]=filters.to_date
 base="select h.name reference,h.posting_date date,h.project,hi.item_code item,hi.short_qty quantity,hi.discrepancy_type classification,h.discrepancy_status status from `tabStock Handover` h join `tabStock Handover Item` hi on hi.parent=h.name where h.docstatus<2 and h.discrepancy_status!='None'"
 tail=""
 for marker in (" group by "," having "):
  if marker in base.lower():
   pos=base.lower().find(marker);tail=base[pos:];base=base[:pos];break
 sql=base + (" AND " + " AND ".join(conditions) if conditions else "") + tail
 data=frappe.db.sql(sql,values,as_dict=True)
 for row in data:
  if row.get("item"): row["item__title"]=frappe.db.get_value("Item",row.item,"item_name") or row.item
  row["reference__title"]=row.get("reference")
 columns=[{"label":_("Reference"),"fieldname":"reference","fieldtype":"Link","options":"Stock Handover","width":150},{"label":_("Date"),"fieldname":"date","fieldtype":"Date","width":100},{"label":_("Party or Asset"),"fieldname":"party","width":160},{"label":_("Item"),"fieldname":"item","fieldtype":"Link","options":"Item","width":140},{"label":_("Project"),"fieldname":"project","fieldtype":"Link","options":"Project","width":140},{"label":_("Classification"),"fieldname":"classification","width":150},{"label":_("Quantity"),"fieldname":"quantity","fieldtype":"Float","width":100},{"label":_("Value"),"fieldname":"value","fieldtype":"Currency","width":120},{"label":_("Status"),"fieldname":"status","width":130}]
 present={k for row in data for k in row.keys()};columns=[c for c in columns if c["fieldname"] in present or c["fieldname"] in ("reference","date")]
 if "value" in () and not set(frappe.get_roles()).intersection({"System Manager","Accounts Manager","Accounts User","Finance Reviewer"}):columns=[c for c in columns if c["fieldname"]!="value"];[r.pop("value",None) for r in data]
 summary=[{"label":_("Records"),"value":len(data),"indicator":"Blue"},{"label":_("Open or Pending"),"value":sum(1 for r in data if any(x in str(r.get("status") or "").lower() for x in ("open","pending","overdue","review"))),"indicator":"Orange"},{"label":_("Total Quantity"),"value":sum((r.get("quantity") or 0) for r in data),"indicator":"Green"}]
 return columns,data,None,None,summary
