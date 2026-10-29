frappe.ui.form.on("Website Settings", {
  refresh(frm) {
    if (frm.doc.qorg_opportunity_portal_enabled) {
      frm.add_custom_button(__("Open Opportunity Portal"), () => {
        window.open("/opportunities", "_blank", "noopener");
      }, __("Opportunity Portal"));

      frm.add_custom_button(__("Open Portal Settings"), () => {
        frappe.set_route("Form", "Portal Settings", "Portal Settings");
      }, __("Opportunity Portal"));
    }

    if (frm.doc.qorg_enable_enhanced_web_form_design) {
      frm.add_custom_button(__("Preview Web Form Design"), () => {
        window.open("/external-profile-form/new", "_blank", "noopener");
      }, __("Web Form Appearance"));
    }

    frm.add_custom_button(__("Use Recommended Design Defaults"), async () => {
      await frm.set_value({
        qorg_enable_enhanced_web_form_design: 1,
        qorg_web_form_use_company_branding: 1,
        qorg_web_form_show_hero_header: 1,
        qorg_web_form_show_privacy_notice: 1,
        qorg_web_form_sticky_actions: 1,
        qorg_web_form_hide_child_row_name: 1,
        qorg_web_form_max_content_width: 1180,
      });
      frappe.show_alert({ message: __("Recommended Web Form design defaults applied."), indicator: "green" });
    }, __("Web Form Appearance"));
  },

  qorg_opportunity_portal_page_size(frm) {
    const value = Number(frm.doc.qorg_opportunity_portal_page_size || 24);
    if (value < 6 || value > 50) {
      frappe.msgprint(__("Opportunities per Page must be between 6 and 50."));
    }
  },

  qorg_web_form_max_content_width(frm) {
    const value = Number(frm.doc.qorg_web_form_max_content_width || 1180);
    if (value < 760 || value > 1600) {
      frappe.msgprint(__("Web Form Maximum Content Width must be between 760 and 1600 pixels."));
    }
  },
});
