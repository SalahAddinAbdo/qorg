function qorg_budget_line_tree_project(treeview) {
    const control = treeview && treeview.page && treeview.page.fields_dict
        ? treeview.page.fields_dict.project
        : null;
    return control && control.get_value ? control.get_value() : null;
}

function qorg_open_budget_line_full_form(treeview, node) {
    const defaults = {};
    const project = qorg_budget_line_tree_project(treeview);
    if (project) defaults.project = project;

    const value = node && node.data && (node.data.value || node.data.name);
    if (value && value !== "Budget Line" && value !== __("Budget Lines")) {
        defaults.parent_budget_line = value;
        if (node.data.project && !defaults.project) defaults.project = node.data.project;
    }

    frappe.new_doc("Budget Line", defaults);
}

function qorg_bind_budget_line_tree_actions(treeview) {
    if (!treeview || !treeview.page) return;

    treeview.page.set_primary_action(__("Add Budget Line"), () => {
        qorg_open_budget_line_full_form(treeview, null);
    });

    // The standard Tree toolbar calls settings.add_node(node). Redirect that
    // path to the full form so the reduced Tree dialog is never used.
    frappe.treeview_settings["Budget Line"].add_node = (node) => {
        qorg_open_budget_line_full_form(treeview, node);
    };
}

frappe.treeview_settings["Budget Line"] = {
    breadcrumb: "QOrg",
    title: __("Budget Lines"),
    root_label: __("Budget Lines"),
    filters: [
        {
            fieldname: "project",
            fieldtype: "Link",
            options: "Project",
            label: __("Project")
        }
    ],
    // These fields remain descriptive metadata for the Tree API, but creation
    // is redirected to the full Budget Line form by the handlers below.
    fields: [],
    onload(treeview) {
        qorg_bind_budget_line_tree_actions(treeview);
    },
    post_render(treeview) {
        qorg_bind_budget_line_tree_actions(treeview);
    },
    extend_toolbar: true
};
