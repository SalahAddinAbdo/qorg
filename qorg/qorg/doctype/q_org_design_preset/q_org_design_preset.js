frappe.ui.form.on("Q Org Design Preset",{refresh(frm){if(!frm.is_new())frm.add_custom_button(__("Open Design System Settings"),()=>frappe.set_route("Form","Q Org Design System Settings"));}});
