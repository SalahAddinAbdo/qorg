frappe.ui.form.on("Q Org Design System Settings", {
  refresh(frm) {
    frm.set_intro(__("Desk remains on Frappe Standard. This phase controls only the login experience, language access and Quick Create configuration."), "blue");
  },
});
