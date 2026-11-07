from frappe import _


def get_data(data=None):
    """Extend ERPNext's existing Material Request dashboard data.

    Frappe v16 passes the current dashboard bundle as the keyword argument
    ``data`` to every ``override_doctype_dashboards`` hook. The hook must
    accept that argument and return the merged dashboard bundle.
    """
    data = data or {}

    non_standard = data.setdefault("non_standard_fieldnames", {})
    non_standard["Procurement Process"] = "material_request"

    transactions = data.setdefault("transactions", [])
    qorg_items = ["Procurement Process"]

    existing_group = next(
        (row for row in transactions if row.get("label") == _("QOrg Procurement")),
        None,
    )

    if existing_group:
        existing_items = existing_group.setdefault("items", [])
        for item in qorg_items:
            if item not in existing_items:
                existing_items.append(item)
    else:
        transactions.append(
            {
                "label": _("QOrg Procurement"),
                "items": qorg_items,
            }
        )

    return data
