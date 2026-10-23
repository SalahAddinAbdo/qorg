from __future__ import annotations
import hashlib,json,frappe
from frappe.utils import now_datetime
INTERFACE_PREFIX="Interface Policy::"; DENY_ROLE="QOrg Disabled Component"; SUPPORTED_TYPES={"Report","Page","Workspace"}
def _key(t,n): return f"{INTERFACE_PREFIX}{t}::{n}"
def _ensure_deny_role():
 if not frappe.db.exists("Role",DENY_ROLE): frappe.get_doc({"doctype":"Role","role_name":DENY_ROLE,"desk_access":0,"disabled":1}).insert(ignore_permissions=True)
 return DENY_ROLE
def _roles(doc): return sorted({r.role for r in (getattr(doc,"roles",None) or []) if getattr(r,"role",None)})
def _snapshot(t,n):
 doc=frappe.get_doc(t,n); return {"roles":_roles(doc),"public":int(getattr(doc,"public",0) or 0),"is_hidden":int(getattr(doc,"is_hidden",0) or 0)}
def _save(t,n,v,snapshot,allowed):
 key=_key(t,n); state=frappe.get_doc("Managed Configuration State",key) if frappe.db.exists("Managed Configuration State",key) else frappe.new_doc("Managed Configuration State")
 details={"component_type":t,"component_name":n,"visibility":v,"snapshot":snapshot,"allowed_roles":allowed}
 state.component_type="Other"; state.component_key=key; state.management_status="Managed"; state.last_checked_on=now_datetime(); state.last_seen_fingerprint=v; state.applied_fingerprint=hashlib.sha256(json.dumps(details,sort_keys=True,separators=(",",":")).encode()).hexdigest(); state.details=json.dumps(details,sort_keys=True); state.flags.ignore_permissions=True; state.save()
def _set_roles(t,n,roles):
 doc=frappe.get_doc(t,n)
 if not doc.meta.has_field("roles"): frappe.throw(f"{t} {n} does not support role-based access.")
 doc.set("roles",[{"role":r} for r in roles]); doc.flags.ignore_permissions=True; doc.save()
def restore_interface_policy(t,n):
 key=_key(t,n)
 if frappe.db.exists("Managed Configuration State",key):
  state=frappe.get_doc("Managed Configuration State",key); details=frappe.parse_json(state.details) or {}; _set_roles(t,n,(details.get("snapshot") or {}).get("roles") or []); frappe.delete_doc("Managed Configuration State",key,ignore_permissions=True,force=True)
 frappe.clear_cache(); return "Visible"
def apply_interface_policy(t,n,v,allowed_roles=None):
 if frappe.session.user!="Administrator": frappe.throw("Only Administrator can apply interface policies.",frappe.PermissionError)
 if t not in SUPPORTED_TYPES: frappe.throw(f"Policy application for {t} is not enabled yet.")
 if v=="Visible": return restore_interface_policy(t,n)
 key=_key(t,n); state=frappe.get_doc("Managed Configuration State",key) if frappe.db.exists("Managed Configuration State",key) else None; snapshot=(frappe.parse_json(state.details) or {}).get("snapshot") if state else _snapshot(t,n)
 allowed=[r.strip() for r in (allowed_roles or "").split(",") if r.strip()]
 for role in allowed:
  if not frappe.db.exists("Role",role): frappe.throw(f"Role {role} does not exist.")
 effective=allowed if v=="Restricted" and allowed else [_ensure_deny_role()]
 _set_roles(t,n,effective); _save(t,n,v,snapshot,allowed); frappe.clear_cache(); return v
def active_interface_policies():
 out={}
 for row in frappe.get_all("Managed Configuration State",filters={"component_key":("like",f"{INTERFACE_PREFIX}%")},fields=["details"]):
  d=frappe.parse_json(row.details) or {}; t=d.get("component_type"); n=d.get("component_name")
  if t and n: out[(t,n)]=d
 return out
def get_interface_policy(t,n): return active_interface_policies().get((t,n),{}).get("visibility","Visible")
