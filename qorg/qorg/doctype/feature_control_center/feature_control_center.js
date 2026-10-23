frappe.ui.form.on("Feature Control Center", {
 refresh(frm) {
  frm.set_intro(__("Document policies use native Frappe permissions. Interface inventory is managed separately. Administrator remains the recovery account."),"blue");
  const call=(method,args={})=>frappe.call({method:`qorg.qorg.enterprise_foundation.api.${method}`,args,freeze:true,callback:()=>frm.reload_doc()});
  frm.add_custom_button(__("Synchronize Inventory"),()=>call("synchronize_models"),__("Inventory"));
  frm.add_custom_button(__("Audit Configuration"),()=>call("audit_control_center"),__("Inventory"));
  frm.add_custom_button(__("Preview Changes"),()=>call("preview_model_changes"),__("Changes"));
  frm.add_custom_button(__("Apply Safe Changes"),()=>frappe.confirm(__("Apply reviewed safe changes?"),()=>call("apply_model_changes")),__("Changes"));
 }
});
