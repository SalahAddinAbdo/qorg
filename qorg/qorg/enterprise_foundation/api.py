from __future__ import annotations
import json,frappe
from frappe.utils import now_datetime
from qorg.qorg.enterprise_foundation.audit import audit_company_settings as _audit_company,audit_control_center as _audit_center
from qorg.qorg.enterprise_foundation.constants import CONFIGURATION_VERSION,CRITICAL_DOCTYPES
from qorg.qorg.enterprise_foundation.model_registry import scan_models
from qorg.qorg.enterprise_foundation.permissions import require_administrator
def _center(): require_administrator(); return frappe.get_single("Feature Control Center")
@frappe.whitelist()
def synchronize_models():
 doc=_center(); existing={r.document_type:r for r in (doc.models or [])}; doc.set("models",[])
 for data in scan_models():
  old=existing.get(data["document_type"])
  if old and data["model_kind"]!="Child Table": data.update({"requested_policy":old.requested_policy or data["current_policy"],"requested_action_policy":old.requested_action_policy or data["current_action_policy"],"change_reason":old.change_reason})
  doc.append("models",data)
 doc.last_synchronized_on=now_datetime(); doc.last_synchronized_by=frappe.session.user; doc.configuration_version=CONFIGURATION_VERSION; doc.pending_change_count=sum(1 for r in doc.models if r.model_kind!="Child Table" and (r.current_policy!=r.requested_policy or r.current_action_policy!=r.requested_action_policy)); doc.flags.ignore_permissions=True; doc.save(); return {"models":len(doc.models),"pending":doc.pending_change_count}
def _changes(doc):
 out=[]
 for r in doc.models or []:
  if r.model_kind=="Child Table" or (r.current_policy==r.requested_policy and r.current_action_policy==r.requested_action_policy):continue
  out.append({"document_type":r.document_type,"access_from":r.current_policy,"access_to":r.requested_policy,"action_from":r.current_action_policy,"action_to":r.requested_action_policy,"allowed":r.document_type not in CRITICAL_DOCTYPES and r.risk_level!="Blocked","risk":r.risk_level,"reason":r.change_reason})
 return out
@frappe.whitelist()
def preview_model_changes():
 doc=_center(); changes=_changes(doc); doc.last_preview=json.dumps(changes,default=str,indent=2); doc.pending_change_count=len(changes); doc.flags.ignore_permissions=True; doc.save(); return changes
@frappe.whitelist(methods=["POST"])
def apply_model_changes():
 doc=_center(); preview=_changes(doc)
 if [x for x in preview if not x["allowed"]]: frappe.throw("Blocked or critical model changes must be removed before applying.")
 from qorg.qorg.enterprise_foundation.model_policy_engine import active_action_policies,active_native_policies,apply_action_policy,apply_model_policy
 applied=[]
 for r in doc.models or []:
  if r.model_kind=="Child Table":continue
  ac=r.current_policy!=r.requested_policy; aa=r.current_action_policy!=r.requested_action_policy
  if not ac and not aa:continue
  if not r.change_reason:frappe.throw(f"Change reason is required for {r.document_type}.")
  if ac:r.current_policy=apply_model_policy(r.document_type,r.requested_policy); r.requested_policy=r.current_policy
  if aa:r.current_action_policy=apply_action_policy(r.document_type,r.requested_action_policy,allow_print=r.allow_print,allow_email=r.allow_email,allow_comments=r.allow_comments,allow_attachments=r.allow_attachments); r.requested_action_policy=r.current_action_policy
  applied.append(r.document_type)
 access=active_native_policies(); actions=active_action_policies(); doc.last_preview=json.dumps(preview,default=str,indent=2); doc.pending_change_count=0; doc.last_apply_summary=f"Applied {len(applied)} model changes. Active access policies: {len(access)}. Active action policies: {len(actions)}."; doc.flags.ignore_permissions=True; doc.save(); frappe.clear_cache(); frappe.publish_realtime("qorg_model_policy_changed",{"changed":applied},after_commit=True); return {"applied":applied,"access":access,"actions":actions}
@frappe.whitelist()
def audit_control_center():
 doc=_center(); doc.set("audit_results",[])
 for f in _audit_center(doc):doc.append("audit_results",f)
 doc.flags.ignore_permissions=True; doc.save(); return {"findings":len(doc.audit_results)}
@frappe.whitelist()
def get_model_policies():
 from qorg.qorg.enterprise_foundation.model_policy_engine import active_native_policies
 return active_native_policies()
@frappe.whitelist()
def get_action_policies():
 from qorg.qorg.enterprise_foundation.model_policy_engine import active_action_policies
 return active_action_policies()
@frappe.whitelist()
def audit_company_settings(settings_name:str):
 require_administrator(); doc=frappe.get_doc("Company Feature Settings",settings_name); issues=_audit_company(doc); doc.last_audited_on=now_datetime(); doc.last_audit_summary="\n".join(issues) if issues else "No configuration issues detected."; doc.flags.ignore_permissions=True; doc.save(); return {"issues":issues}
