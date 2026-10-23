frappe.listview_settings["Managed Configuration State"] = {
    hide_name_column: false,
    onload(listview) {
        listview.page.clear_primary_action();
        listview.page.clear_actions_menu();
        listview.page.clear_inner_toolbar();

        listview.page.add_inner_button(__("Feature Control Center"), () => {
            frappe.set_route("Form", "Feature Control Center");
        });
    },
    get_indicator(doc) {
        const colors = {
            Managed: "green",
            "Administrator Modified": "orange",
            Adopted: "blue",
            Conflict: "red",
            Missing: "red",
            Restored: "gray"
        };
        return [
            __(doc.management_status || "Unknown"),
            colors[doc.management_status] || "gray",
            `management_status,=,${doc.management_status}`
        ];
    }
};
