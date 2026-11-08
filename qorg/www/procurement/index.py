import frappe


def get_context(context):
    context.no_cache = 1
    search = (frappe.form_dict.get("search") or "").strip()
    notice_type = (frappe.form_dict.get("notice_type") or "").strip()
    procurement_type = (frappe.form_dict.get("procurement_type") or "").strip()

    filters = {"published": 1, "docstatus": 1}
    if notice_type:
        filters["notice_type"] = notice_type

    or_filters = None
    if search:
        like = f"%{search}%"
        or_filters = {"title": ["like", like], "summary": ["like", like], "name": ["like", like]}

    notices = frappe.get_all(
        "Procurement Notice",
        filters=filters,
        or_filters=or_filters,
        fields=["name", "title", "notice_type", "deadline", "route", "summary", "procurement_process"],
        order_by="deadline asc",
    )
    process_names = [row.procurement_process for row in notices if row.procurement_process]
    process_map = {
        row.name: row
        for row in frappe.get_all(
            "Procurement Process",
            filters={"name": ["in", process_names]},
            fields=["name", "procurement_type", "procurement_method", "currency"],
        )
    } if process_names else {}
    for row in notices:
        process = process_map.get(row.procurement_process)
        row.procurement_type = process.procurement_type if process else None
    if procurement_type:
        notices = [row for row in notices if row.procurement_type == procurement_type]

    context.notices = notices
    context.filters = {"search": search, "notice_type": notice_type, "procurement_type": procurement_type}
    context.notice_types = sorted(set(frappe.get_all("Procurement Notice", filters={"published": 1, "docstatus": 1}, pluck="notice_type")))
    context.procurement_types = ["Goods", "Services", "Works", "Consultancy", "Mixed"]
    return context
