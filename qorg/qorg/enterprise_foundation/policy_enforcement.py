import frappe
from qorg.qorg.enterprise_foundation.model_policy_engine import active_action_policies,active_native_policies
CONTROL={"Feature Control Center","Model Control Entry","Interface Control Entry","Configuration Audit Result","Managed Configuration State"}
def get_model_policy(dt): return active_native_policies().get(dt,"Enabled") if dt else "Enabled"
def get_policy_map(): return active_native_policies()
def _bypass(): return frappe.session.user=="Administrator" or getattr(frappe.flags,"in_install",False) or getattr(frappe.flags,"in_migrate",False)
def enforce_model_policy(doc,method=None):
 if _bypass() or getattr(doc,"doctype",None) in CONTROL:return
 if get_model_policy(getattr(doc,"doctype",None)) in {"Read Only","Restricted","Feature Disabled","Deprecated"}: frappe.throw(f"{doc.doctype} cannot be changed under the active policy.",frappe.PermissionError)
def enforce_rename_policy(dt):
 if not _bypass() and get_model_policy(dt) in {"Read Only","Restricted","Feature Disabled","Deprecated"}: frappe.throw(f"{dt} cannot be renamed or merged under the active policy.",frappe.PermissionError)
def enforce_comment_policy(doc,method=None):
 if _bypass():return
 dt=getattr(doc,"reference_doctype",None); cfg=active_action_policies().get(dt,{})
 if cfg.get("policy")=="View Only" and not int(cfg.get("allow_comments",1)): frappe.throw(f"Adding comments to {dt} is disabled.",frappe.PermissionError)
def enforce_file_policy(doc,method=None):
 if _bypass():return
 dt=getattr(doc,"attached_to_doctype",None); cfg=active_action_policies().get(dt,{})
 if cfg.get("policy")=="View Only" and not int(cfg.get("allow_attachments",1)): frappe.throw(f"Adding or removing attachments for {dt} is disabled.",frappe.PermissionError)
