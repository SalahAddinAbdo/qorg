frappe.ui.form.on("Web Form", {
  refresh(frm) {
    if (!frm.doc.route) return;

    frm.add_custom_button(__("Preview Web Form"), () => {
      window.open(`/${frm.doc.route}`, "_blank", "noopener");
    }, __("Enhanced Design"));

    frm.add_custom_button(__("Inherit Global Design"), async () => {
      await frm.set_value({
        qorg_web_form_design_mode: "Use Global Setting",
        qorg_web_form_branding_company: "",
        qorg_web_form_max_content_width_override: 0,
        qorg_web_form_hero_mode: "Use Global Setting",
        qorg_web_form_privacy_notice_mode: "Use Global Setting",
        qorg_web_form_sticky_actions_mode: "Use Global Setting",
        qorg_web_form_child_name_mode: "Use Global Setting",
      });
      frappe.show_alert({ message: __("This Web Form now inherits the global Website Settings design."), indicator: "green" });
    }, __("Enhanced Design"));
  },

  qorg_web_form_max_content_width_override(frm) {
    const width = Number(frm.doc.qorg_web_form_max_content_width_override || 0);
    if (width && (width < 760 || width > 1600)) {
      frappe.msgprint(__("Maximum Content Width Override must be between 760 and 1600 pixels, or left blank."));
    }
  },
});
