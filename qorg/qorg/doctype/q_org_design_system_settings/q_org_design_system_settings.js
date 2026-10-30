frappe.ui.form.on("Q Org Design System Settings", {
  refresh(frm) {
    frm.add_custom_button(__("Preview"), async () => {
      const response = await frappe.call({
        method: "qorg.qorg.design_system.api.preview",
        type: "POST",
        args: { configuration: JSON.stringify(frm.doc) },
      });
      window.qorgDesignSystem?.preview(response.message);
    }, __("Design System"));

    frm.add_custom_button(__("Apply"), async () => {
      await frm.save();
      await frappe.call({ method: "qorg.qorg.design_system.api.apply", type: "POST", freeze: true });
      window.location.reload();
    }, __("Design System"));

    frm.add_custom_button(__("Validate"), async () => {
      const response = await frappe.call("qorg.qorg.design_system.api.validate_current_configuration");
      const findings = response.message?.findings || [];
      if (!findings.length) return frappe.show_alert({ message: __("Configuration is valid."), indicator: "green" });
      frappe.msgprint({ title: __("Design System Validation"), indicator: "orange", message: findings.map((row) => `<p><strong>${frappe.utils.escape_html(row.severity)}</strong>: ${frappe.utils.escape_html(row.message)}</p>`).join("") });
    }, __("Design System"));

    frm.add_custom_button(__("Restore Frappe Default"), () => {
      frappe.confirm(__("Restore the standard Frappe appearance?"), async () => {
        await frappe.call({ method: "qorg.qorg.design_system.api.restore_frappe_default", type: "POST", freeze: true });
        window.location.reload();
      });
    }, __("Design System"));

    frm.add_custom_button(__("Clone Active Preset"), () => {
      if (!frm.doc.active_preset) return frappe.msgprint(__("Select an active preset first."));
      frappe.prompt({ fieldname: "name", fieldtype: "Data", label: __("New Preset Name"), reqd: 1 }, async (values) => {
        const response = await frappe.call({ method: "qorg.qorg.design_system.api.clone_preset", type: "POST", args: { source: frm.doc.active_preset, target: values.name }, freeze: true });
        frappe.set_route("Form", "Q Org Design Preset", response.message.name);
      }, __("Clone Preset"), __("Clone"));
    }, __("Presets"));

    frm.add_custom_button(__("Export Active Preset"), async () => {
      if (!frm.doc.active_preset) return frappe.msgprint(__("Select an active preset first."));
      const response = await frappe.call("qorg.qorg.design_system.api.export_preset", { name: frm.doc.active_preset });
      const blob = new Blob([JSON.stringify(response.message, null, 2)], { type: "application/json" });
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = `${frm.doc.active_preset.replace(/[^a-z0-9_-]+/gi, "-")}.json`;
      link.click();
      URL.revokeObjectURL(link.href);
    }, __("Presets"));

    frm.add_custom_button(__("Import Preset"), () => {
      const dialog = new frappe.ui.Dialog({
        title: __("Import Design Preset"),
        fields: [
          { fieldname: "name", fieldtype: "Data", label: __("Preset Name"), reqd: 1 },
          { fieldname: "payload", fieldtype: "Code", label: __("Preset JSON"), options: "JSON", reqd: 1 },
        ],
        primary_action_label: __("Import"),
        primary_action: async (values) => {
          const response = await frappe.call({ method: "qorg.qorg.design_system.api.import_preset", type: "POST", args: { payload: values.payload, target: values.name }, freeze: true });
          dialog.hide();
          frappe.set_route("Form", "Q Org Design Preset", response.message.name);
        },
      });
      dialog.show();
    }, __("Presets"));
  },

  async active_preset(frm) {
    if (!frm.doc.active_preset || frm.__qorg_loading_preset) return;
    frm.__qorg_loading_preset = true;
    try {
      const response = await frappe.call("qorg.qorg.design_system.api.get_preset_configuration", { name: frm.doc.active_preset });
      for (const [fieldname, value] of Object.entries(response.message || {})) {
        if (frm.fields_dict[fieldname]) await frm.set_value(fieldname, value);
      }
    } finally {
      frm.__qorg_loading_preset = false;
    }
  },
});
