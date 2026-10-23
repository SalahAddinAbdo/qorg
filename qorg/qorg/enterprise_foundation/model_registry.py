from __future__ import annotations
import hashlib,json,frappe
from frappe.utils import now_datetime
from qorg.qorg.enterprise_foundation.constants import CRITICAL_DOCTYPES
from qorg.qorg.enterprise_foundation.model_policy_engine import active_native_policies,active_action_policies
def _app(module): return frappe.db.get_value("Module Def",module,"app_name") if module else ""
def _ownership(app,custom):
 if custom:return "Custom from UI"
 return {"frappe":"Framework Standard","erpnext":"ERPNext Standard","hrms":"HRMS Standard","qorg":"QOrg Standard"}.get(app,"Other App Standard")
def _kind(r): return "Virtual" if r.is_virtual else "Child Table" if r.istable else "Single" if r.issingle else "Main"
def _risk(name,app,kind,count):
 if name in CRITICAL_DOCTYPES or kind=="Child Table":return "Blocked"
 if app in ("frappe","erpnext","hrms"):return "High"
 return "Medium" if count else "Low"
def scan_models():
 rows=frappe.get_all("DocType",fields=["name","module","custom","istable","issingle","is_virtual"],order_by="module asc,name asc"); access=active_native_policies(); actions=active_action_policies(); reports=set(frappe.get_all("Report",pluck="ref_doctype")); workflows=set(frappe.get_all("Workflow",filters={"is_active":1},pluck="document_type")); out=[]; now=now_datetime()
 for r in rows:
  app=_app(r.module); kind=_kind(r); count=0 if kind in ("Single","Virtual") else frappe.db.count(r.name); a=access.get(r.name,"Enabled") if kind!="Child Table" else "Enabled"; cfg=actions.get(r.name,{}) if kind!="Child Table" else {}
  data={"document_type":r.name,"document_label":r.name,"app_name":app,"module_name":r.module,"model_kind":kind,"ownership_type":_ownership(app,r.custom),"current_policy":a,"requested_policy":a,"current_action_policy":cfg.get("policy","Standard"),"requested_action_policy":cfg.get("policy","Standard"),"risk_level":_risk(r.name,app,kind,count),"record_count":count,"incoming_links":frappe.db.count("DocField",{"fieldtype":"Link","options":r.name})+frappe.db.count("Custom Field",{"fieldtype":"Link","options":r.name}),"has_workflow":r.name in workflows,"has_reports":r.name in reports,"has_workspace_links":bool(frappe.db.exists("Workspace Link",{"link_to":r.name})) if frappe.db.exists("DocType","Workspace Link") else False,"allow_print":cfg.get("allow_print",1),"allow_email":cfg.get("allow_email",1),"allow_comments":cfg.get("allow_comments",1),"allow_attachments":cfg.get("allow_attachments",1),"last_synchronized_on":now}
  data["scan_fingerprint"]=hashlib.sha256(json.dumps(data,default=str,sort_keys=True).encode()).hexdigest(); out.append(data)
 return out
