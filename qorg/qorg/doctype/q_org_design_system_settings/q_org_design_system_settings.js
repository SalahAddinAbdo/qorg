frappe.ui.form.on("Q Org Design System Settings", {
    refresh(frm) {
        frm.set_intro(__("Desk, navigation, workspace and web tokens are independent. Light and dark values follow the standard Appearance selection."), "blue");
    },

    font_source(frm) {
        if (frm.doc.font_source === "Google Fonts" && !frm.doc.font_stylesheet_url) {
            frappe.show_alert({
                message: __("Add the official Google Fonts CSS2 URL and only the weights you need."),
                indicator: "blue",
            });
        }
    },

    after_save() {
        localStorage.removeItem("qorg-theme-runtime-v1.3");
        localStorage.removeItem("qorg-theme-runtime-v1.3.1");
        localStorage.removeItem("qorg-ui-tokens-v1.2");
        localStorage.removeItem("qorg-ui-tokens-v1.3.1");

        if (typeof window.qorg_refresh_theme === "function") {
            window.qorg_refresh_theme().then(() => {
                frappe.show_alert({message: __("Theme settings applied."), indicator: "green"});
            });
            return;
        }

        frappe.show_alert({message: __("Theme settings saved. Reloading interface..."), indicator: "green"});
        window.setTimeout(() => window.location.reload(), 250);
    },
});
