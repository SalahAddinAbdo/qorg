frappe.ui.form.on("Q Org Design System Settings", {
  refresh(frm) {
    frm.set_intro(__("Frappe Standard baseline is active. Quick Create configuration and language access are preserved."), "blue");
  },
});
