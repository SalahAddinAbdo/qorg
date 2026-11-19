import frappe
from frappe import _
from frappe.utils import flt

def selected(filters,key):
 value=(filters or {}).get(key) or []
 if isinstance(value,str): value=frappe.parse_json(value) if value.startswith("[") else [x.strip() for x in value.split(",") if x.strip()]
 return value

def in_selected(value,filters,key):
 values=selected(filters,key);return not values or value in values

def apply_view(columns,mode):
 modes={"Executive":{"source_voucher","source_account","exception_message","rule_snapshot"},"Donor":{"source_voucher","source_account","source_cost_center","rule_snapshot"},"Operations":{"rule_snapshot"},"Audit":set()}
 hidden=modes.get(mode or "Executive",set())
 return [c for c in columns if c.get("fieldname") not in hidden]

def chart_by(rows,key,value,label):
 totals={}
 for row in rows:
  name=row.get(key) or _("Unspecified");totals[name]=totals.get(name,0)+flt(row.get(value))
 ordered=sorted(totals.items(),key=lambda x:abs(x[1]),reverse=True)[:12]
 return {"data":{"labels":[x[0] for x in ordered],"datasets":[{"name":label,"values":[x[1] for x in ordered]}]},"type":"bar","colors":["#137690"]} if ordered else None

def summary(items):
 return [{"label":label,"value":value,"datatype":datatype,"indicator":indicator} for label,value,datatype,indicator in items]
