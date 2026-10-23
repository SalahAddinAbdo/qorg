import frappe
from qorg.qorg.enterprise_foundation.model_policy_engine import active_native_policies
CONTROL_DOCTYPES={"Feature Control Center","Model Control Entry","Configuration Audit Result","Managed Configuration State"}
def get_model_policy(dt): return active_native_policies().get(dt,"Enabled") if dt else "Enabled"
def get_policy_map(): return active_native_policies()
def enforce_model_policy(doc,method=None):
 if frappe.session.user=="Administrator" or getattr(doc,"doctype",None) in CONTROL_DOCTYPES or getattr(frappe.flags,"in_install",False) or getattr(frappe.flags,"in_migrate",False): return
 if get_model_policy(getattr(doc,"doctype",None)) in {"Read Only","Restricted","Feature Disabled","Deprecated"}: frappe.throw(f"{doc.doctype} cannot be changed under the active model policy.",frappe.PermissionError)
def enforce_rename_policy(dt):
 if frappe.session.user!="Administrator" and get_model_policy(dt) in {"Read Only","Restricted","Feature Disabled","Deprecated"}: frappe.throw(f"{dt} cannot be renamed or merged under the active model policy.",frappe.PermissionError)
