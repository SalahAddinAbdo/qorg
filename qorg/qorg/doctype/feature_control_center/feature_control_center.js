frappe.ui.form.on("Feature Control Center",{refresh(frm){
 const call=(method,args={})=>frappe.call({method,args,freeze:true,callback:()=>frm.reload_doc()});
 frm.add_custom_button(__("Synchronize Inventory"),()=>call("qorg.qorg.enterprise_foundation.api.synchronize_models"),__("Inventory"));
 frm.add_custom_button(__("Audit Configuration"),()=>call("qorg.qorg.enterprise_foundation.api.audit_control_center"),__("Inventory"));
 frm.add_custom_button(__("Preview Changes"),async()=>{const m=await frappe.call({method:"qorg.qorg.enterprise_foundation.api.preview_model_changes",freeze:true});const i=await frappe.call({method:"qorg.qorg.enterprise_foundation.interface_api.preview_interface_changes",freeze:true});frappe.msgprint(__("Document changes: {0}<br>Interface changes: {1}",[m.message?.length||0,i.message?.length||0]));frm.reload_doc()},__("Changes"));
 frm.add_custom_button(__("Apply Safe Changes"),()=>frappe.confirm(__("Apply reviewed changes?"),async()=>{await frappe.call({method:"qorg.qorg.enterprise_foundation.api.apply_model_changes",freeze:true});await frappe.call({method:"qorg.qorg.enterprise_foundation.interface_api.apply_interface_changes",freeze:true});frm.reload_doc()}),__("Changes"));
}});
