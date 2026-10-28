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
    fields: [
        {
            fieldname: "project",
            fieldtype: "Link",
            options: "Project",
            label: __("Project"),
            reqd: 1
        },
        {
            fieldname: "is_group",
            fieldtype: "Check",
            label: __("Is Group")
        },
        {
            fieldname: "parent_budget_line",
            fieldtype: "Link",
            options: "Budget Line",
            label: __("Parent Budget Line")
        },
        {
            fieldname: "name1",
            fieldtype: "Data",
            label: __("Name"),
            reqd: 1
        }
    ]
};
