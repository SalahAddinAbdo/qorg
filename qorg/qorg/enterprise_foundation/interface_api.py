import frappe
from qorg.qorg.enterprise_foundation.interface_policy_engine import active_interface_policies,apply_interface_policy
from qorg.qorg.enterprise_foundation.permissions import require_administrator
@frappe.whitelist()
def preview_interface_changes():
 require_administrator(); center=frappe.get_single("Feature Control Center"); active=active_interface_policies(); out=[]
 for row in center.interface_components or []:
  effective=active.get((row.component_type,row.component_name),{}).get("visibility","Visible")
  if effective!=row.requested_visibility: out.append({"component_type":row.component_type,"component_name":row.component_name,"from":effective,"to":row.requested_visibility,"allowed_roles":row.allowed_roles,"reason":row.change_reason})
 return out
@frappe.whitelist(methods=["POST"])
def apply_interface_changes():
 require_administrator(); center=frappe.get_single("Feature Control Center"); active=active_interface_policies(); applied=[]
 for row in center.interface_components or []:
  effective=active.get((row.component_type,row.component_name),{}).get("visibility","Visible")
  if effective==row.requested_visibility: row.current_visibility=effective; continue
  if not row.change_reason: frappe.throw(f"Change reason is required for {row.component_type} {row.component_name}.")
  row.current_visibility=apply_interface_policy(row.component_type,row.component_name,row.requested_visibility,row.allowed_roles); row.requested_visibility=row.current_visibility; applied.append(f"{row.component_type}: {row.component_name}")
 center.flags.ignore_permissions=True; center.save(); frappe.clear_cache(); return {"applied":applied}
