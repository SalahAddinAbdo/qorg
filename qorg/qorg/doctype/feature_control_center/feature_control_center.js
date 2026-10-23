frappe.ui.form.on("Feature Control Center", {
    refresh(frm) {
        frm.set_intro(__("Site defaults apply only when a company feature is set to Inherit. Site rows cannot inherit."), "blue");
        const call = (method, args = {}) => frappe.call({
            method: `qorg.qorg.enterprise_foundation.api.${method}`,
            args,
            freeze: true,
            callback: () => frm.reload_doc(),
        });

        frm.add_custom_button(__("Synchronize Models"), () => call("synchronize_models"), __("Inventory"));
        frm.add_custom_button(__("Audit Configuration"), () => call("audit_control_center"), __("Inventory"));
        frm.add_custom_button(__("Preview Changes"), () => call("preview_model_changes"), __("Changes"));
        frm.add_custom_button(__("Apply Safe Changes"), () => {
            frappe.confirm(__("Apply the reviewed safe changes?"), () => call("apply_model_changes"));
        }, __("Changes"));
        frm.add_custom_button(__("Restore Defaults"), () => {
            frappe.confirm(__("Restore application-managed defaults without deleting historical data?"), () => call("restore_managed_defaults"));
        }, __("Changes"));
        frm.add_custom_button(__("Export Configuration"), () => call("export_configuration"), __("Inventory"));
    },
});
