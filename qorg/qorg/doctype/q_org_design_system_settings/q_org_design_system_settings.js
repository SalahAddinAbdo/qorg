frappe.ui.form.on("Q Org Design System Settings", {
  refresh(frm) {
    frm.add_custom_button(__("Apply"), async () => { await frm.save(); await frappe.call({method:"qorg.qorg.design_system.api.apply",type:"POST",freeze:true}); window.qorgTheme?.reload?.(); frappe.show_alert({message:__("Theme applied."),indicator:"green"}); });
    frm.add_custom_button(__("Preview"), async () => { const r=await frappe.call({method:"qorg.qorg.design_system.api.preview",type:"POST",args:{configuration:JSON.stringify(frm.doc)}}); window.qorgTheme?.apply?.(r.message,true); });
    frm.add_custom_button(__("Restore Frappe Standard"), async () => { await frappe.call({method:"qorg.qorg.design_system.api.restore_frappe_default",type:"POST",freeze:true}); frm.reload_doc(); window.qorgTheme?.reload?.(); }, __("Actions"));
  }
});
