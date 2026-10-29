frappe.ui.form.on("Website Settings", {
  refresh(frm) {
    if (!frm.doc.qorg_opportunity_portal_enabled) return;
    frm.add_custom_button(__("Open Opportunity Portal"), () => {
      window.open("/opportunities", "_blank", "noopener");
    }, __("Opportunity Portal"));
    frm.add_custom_button(__("Open Portal Settings"), () => {
      frappe.set_route("Form", "Portal Settings", "Portal Settings");
    }, __("Opportunity Portal"));
  },
  qorg_opportunity_portal_page_size(frm) {
    const value = Number(frm.doc.qorg_opportunity_portal_page_size || 24);
    if (value < 6 || value > 50) {
      frappe.msgprint(__("Opportunities per Page must be between 6 and 50."));
    }
  },
});
