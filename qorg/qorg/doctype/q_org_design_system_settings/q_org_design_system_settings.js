frappe.ui.form.on("Q Org Design System Settings", {
    refresh(frm) {
        frm.set_intro(__("Global colors, shape and typography apply to Desk and web. Login settings only control the login layout and slides."), "blue");
        configure_open_item_queries(frm);
    },

    font_source(frm) {
        if (frm.doc.font_source === "Google Fonts" && !frm.doc.font_stylesheet_url) {
            frappe.show_alert({message: __("Add the official Google Fonts CSS2 URL and only the weights you need."), indicator: "blue"});
        }
    },

    after_save() {
        localStorage.removeItem("qorg-ui-tokens-v1.2");
        localStorage.removeItem("qorg-ui-tokens-v1.2.1");
        localStorage.removeItem("qorg-theme-runtime-v1.3");
        frappe.show_alert({message: __("Design settings saved. Reloading the interface to apply all values."), indicator: "green"});
        window.setTimeout(() => window.location.reload(), 250);
    },
});

frappe.ui.form.on("Q Org Open Item", {
    resource_type(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        const keep = {Page: "page", Report: "report", DocType: "reference_doctype"}[row.resource_type];
        ["page", "report", "reference_doctype"].forEach((fieldname) => {
            if (fieldname !== keep) frappe.model.set_value(cdt, cdn, fieldname, null);
        });
        frm.refresh_field("open_items");
    },
});

function configure_open_item_queries(frm) {
    const grid = frm.fields_dict.open_items?.grid;
    if (!grid) return;

    grid.get_field("report").get_query = () => ({filters: {disabled: 0}});
    grid.get_field("reference_doctype").get_query = () => ({filters: {istable: 0}});
}
