from __future__ import annotations
import hashlib,json,frappe
from frappe.permissions import get_rights
from frappe.utils import now_datetime
from qorg.qorg.enterprise_foundation.constants import CONFIGURATION_VERSION
MODEL_PREFIX="Model Policy::"; ACTION_PREFIX="Model Action Policy::"
WRITE_RIGHTS={"write","create","delete","submit","cancel","amend","import","share"}
ALL_RIGHTS={"select","read","write","create","delete","submit","cancel","amend","print","email","report","import","export","share"}
READ_ONLY={"Read Only","Feature Disabled","Deprecated"}
def _state(key): return frappe.get_doc("Managed Configuration State",key) if frappe.db.exists("Managed Configuration State",key) else None
def _hash(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":"),default=str).encode()).hexdigest()
def _payload(row):
 out={"role":row.role,"permlevel":int(row.permlevel or 0),"if_owner":int(row.if_owner or 0)}
 for right in set(get_rights(row.parent))|ALL_RIGHTS:
  if hasattr(row,right): out[right]=int(getattr(row,right) or 0)
 return out
def _snapshot(dt):
 custom=frappe.get_all("Custom DocPerm",filters={"parent":dt},pluck="name",order_by="idx asc")
 if custom:return {"source":"Custom DocPerm","rows":[_payload(frappe.get_doc("Custom DocPerm",n)) for n in custom]}
 standard=frappe.get_all("DocPerm",filters={"parent":dt},pluck="name",order_by="idx asc")
 return {"source":"DocPerm","rows":[_payload(frappe.get_doc("DocPerm",n)) for n in standard]}
def _save(key,details):
 doc=_state(key) or frappe.new_doc("Managed Configuration State"); doc.component_type="Other"; doc.component_key=key; doc.managed_version=CONFIGURATION_VERSION; doc.applied_fingerprint=_hash(details); doc.last_seen_fingerprint=details.get("policy",""); doc.management_status="Managed"; doc.last_checked_on=now_datetime(); doc.details=json.dumps(details,sort_keys=True); doc.flags.ignore_permissions=True; doc.save()
def _replace(dt,rows,policy,allow_print=1,allow_email=1):
 frappe.db.delete("Custom DocPerm",{"parent":dt})
 for idx,base in enumerate(rows,start=1):
  values=dict(base)
  if policy in READ_ONLY:
   for right in WRITE_RIGHTS: values[right]=0
   values["print"]=int(allow_print); values["email"]=int(allow_email)
  elif policy=="Restricted":
   for right in ALL_RIGHTS: values[right]=0
  values.update({"doctype":"Custom DocPerm","parent":dt,"parenttype":"DocType","parentfield":"permissions","idx":idx}); frappe.get_doc(values).insert(ignore_permissions=True)
def apply_model_policy(dt,policy,allow_print=1,allow_email=1):
 if frappe.session.user!="Administrator": frappe.throw("Only Administrator can apply model policies.",frappe.PermissionError)
 key=MODEL_PREFIX+dt; state=_state(key)
 if policy in ("Enabled","Hidden from Navigation"):
  if state:
   details=frappe.parse_json(state.details) or {}; snap=details.get("snapshot") or {}; frappe.db.delete("Custom DocPerm",{"parent":dt})
   if snap.get("source")=="Custom DocPerm": _replace(dt,snap.get("rows") or [],None)
   frappe.delete_doc("Managed Configuration State",state.name,ignore_permissions=True,force=True)
  frappe.clear_cache(doctype=dt); return policy
 snap=(frappe.parse_json(state.details) or {}).get("snapshot") if state else _snapshot(dt)
 if not snap or not snap.get("rows"): frappe.throw(f"{dt} has no role permissions to manage safely.")
 _replace(dt,snap["rows"],policy,allow_print,allow_email); _save(key,{"doctype":dt,"policy":policy,"snapshot":snap}); frappe.clear_cache(doctype=dt); return policy
def apply_action_policy(dt,policy,allow_print=1,allow_email=1,allow_comments=1,allow_attachments=1):
 if policy not in {"Standard","View Only"}: frappe.throw(f"Unsupported action policy: {policy}")
 key=ACTION_PREFIX+dt
 if policy=="Standard":
  if frappe.db.exists("Managed Configuration State",key): frappe.delete_doc("Managed Configuration State",key,ignore_permissions=True,force=True)
  return policy
 _save(key,{"doctype":dt,"policy":policy,"allow_print":int(allow_print),"allow_email":int(allow_email),"allow_comments":int(allow_comments),"allow_attachments":int(allow_attachments)}); return policy
def _active(prefix):
 out={}
 for row in frappe.get_all("Managed Configuration State",filters={"component_key":("like",prefix+"%")},fields=["component_key","details"]):
  details=frappe.parse_json(row.details) or {}; dt=details.get("doctype") or row.component_key.removeprefix(prefix); out[dt]=details
 return out
def active_native_policies(): return {k:v.get("policy") for k,v in _active(MODEL_PREFIX).items() if v.get("policy")}
def active_action_policies(): return {k:{"policy":v.get("policy","Standard"),"allow_print":int(v.get("allow_print",1)),"allow_email":int(v.get("allow_email",1)),"allow_comments":int(v.get("allow_comments",1)),"allow_attachments":int(v.get("allow_attachments",1))} for k,v in _active(ACTION_PREFIX).items()}
