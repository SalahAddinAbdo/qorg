import frappe


def get_context(context):
    context.no_cache = 1
    context.notices = frappe.get_all(
        "Procurement Notice",
        filters={"published": 1, "docstatus": 1},
        fields=["name", "title", "notice_type", "deadline", "route", "summary", "procurement_process"],
        order_by="deadline asc",
    )
    process_names = [row.procurement_process for row in context.notices if row.procurement_process]
    process_types = dict(frappe.get_all("Procurement Process", filters={"name": ["in", process_names]}, fields=["name", "procurement_type"], as_list=True)) if process_names else {}
    for row in context.notices:
        row.procurement_type = process_types.get(row.procurement_process)
    return context
