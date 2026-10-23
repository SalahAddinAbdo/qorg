from __future__ import annotations
import hashlib,json,frappe
from frappe.utils import now_datetime
SPECS=(
 ("Report","Report","name","report_name","module","ref_doctype"),
 ("Page","Page","name","page_name","module",None),
 ("Workspace","Workspace","name","label","module",None),
 ("Dashboard","Dashboard","name","dashboard_name","module",None),
 ("Number Card","Number Card","name","label","module","document_type"),
 ("Web Form","Web Form","name","title","module","doc_type"),
 ("Web Page","Web Page","name","title",None,None),
 ("Print Format","Print Format","name","name","module","doc_type"),
)
def scan_interface_components():
 out=[]; now=now_datetime()
 for kind,dt,namef,labelf,modulef,reff in SPECS:
  if not frappe.db.exists("DocType",dt):continue
  meta=frappe.get_meta(dt); fields=[namef]
  for f in (labelf,modulef,reff):
   if f and meta.has_field(f) and f not in fields:fields.append(f)
  for row in frappe.get_all(dt,fields=fields,order_by=f"{namef} asc"):
   name=row.get(namef); module=row.get(modulef) if modulef else ""; app=frappe.db.get_value("Module Def",module,"app_name") if module else ""
   roles=[]
   try:
    doc=frappe.get_doc(dt,name)
    roles=sorted({getattr(r,"role",None) for r in getattr(doc,"roles",[]) if getattr(r,"role",None)})
   except Exception:pass
   data={"component_type":kind,"component_name":name,"component_label":row.get(labelf) if labelf in fields else name,"app_name":app or "","module_name":module or "","reference_doctype":row.get(reff) if reff and reff in fields else "","current_visibility":"Visible","requested_visibility":"Visible","risk_level":"High" if app in ("frappe","erpnext","hrms") else "Low","roles_summary":", ".join(roles),"last_synchronized_on":now}
   data["scan_fingerprint"]=hashlib.sha256(json.dumps(data,default=str,sort_keys=True).encode()).hexdigest(); out.append(data)
 return out
