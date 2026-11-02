frappe.ui.form.on("Q Org Design System Settings", {
    refresh(frm) {
        frm.set_intro(__("Global colors, shape and typography apply to Desk and web. Login settings only control the login layout and slides."), "blue");
    },
    font_source(frm) {
        if (frm.doc.font_source === "Google Fonts" && !frm.doc.font_stylesheet_url) {
            frappe.show_alert({message: __("Add the official Google Fonts CSS2 URL and only the weights you need."), indicator: "blue"});
        }
    },
});
