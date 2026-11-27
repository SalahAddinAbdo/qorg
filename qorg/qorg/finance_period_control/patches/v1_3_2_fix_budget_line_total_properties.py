import frappe


def execute():
    for property_name in ("read_only", "reqd", "mandatory_depends_on"):
        for name in frappe.get_all(
            "Property Setter",
            filters={
                "doc_type": "Budget Line",
                "field_name": "line_cost",
                "property": property_name,
            },
            pluck="name",
        ):
            frappe.delete_doc("Property Setter", name, ignore_permissions=True, force=True)

    frappe.clear_cache(doctype="Budget Line")
