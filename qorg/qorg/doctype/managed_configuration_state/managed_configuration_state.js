frappe.ui.form.on("Managed Configuration State", {
    refresh(frm) {
        frm.set_intro(
            __(
                "Internal read-only state maintained by Q Org. Apply, restore, and audit configuration through Feature Control Center."
            ),
            "blue"
        );
        frm.disable_save();
        frm.set_read_only();
        frm.page.clear_primary_action();
        frm.page.clear_secondary_action();
        frm.page.clear_actions_menu();
        frm.page.clear_inner_toolbar();
        frm.page.clear_menu();

        frm.add_custom_button(__("Open Feature Control Center"), () => {
            frappe.set_route("Form", "Feature Control Center");
        });
    },
});
