from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt

APPROVED = {"Approved", "Partially Issued", "Fully Issued"}
EPSILON = 0.000001


def issued(material_request_item, current=""):
    """Return net submitted issue quantity after subtracting linked returns."""
    return flt(frappe.db.sql("""
        select coalesce(sum(
            case when ifnull(se.custom_return_against_stock_entry, '') = ''
                 then abs(sed.qty) else -abs(sed.qty) end
        ), 0)
        from `tabStock Entry Detail` sed
        join `tabStock Entry` se on se.name = sed.parent
        where sed.material_request_item = %s
          and se.docstatus = 1
          and se.name != %s
    """, (material_request_item, current))[0][0])


def _original_detail(row, parent_stock_entry):
    detail_name = getattr(row, "custom_return_against_stock_entry_detail", None)
    if detail_name:
        original = frappe.db.get_value(
            "Stock Entry Detail",
            detail_name,
            ["name", "parent", "item_code", "qty", "s_warehouse", "t_warehouse", "batch_no", "serial_no"],
            as_dict=True,
        )
        if not original or original.parent != parent_stock_entry:
            frappe.throw(_("Row {0}: original Stock Entry Detail does not belong to the selected Stock Entry.").format(row.idx))
        return original

    matches = frappe.get_all(
        "Stock Entry Detail",
        filters={"parent": parent_stock_entry, "item_code": row.item_code},
        fields=["name", "parent", "item_code", "qty", "s_warehouse", "t_warehouse", "batch_no", "serial_no"],
        limit=2,
    )
    if len(matches) != 1:
        frappe.throw(_("Row {0}: select Return Against Stock Entry Detail because the original entry has multiple matching rows.").format(row.idx))
    row.custom_return_against_stock_entry_detail = matches[0].name
    return matches[0]


def validate_stock_entry(doc, method=None):
    _validate_activity(getattr(doc, "project", None), getattr(doc, "custom_activity_reference", None))
    material_request = getattr(doc, "custom_material_request", None)
    if doc.purpose == "Material Issue" and material_request:
        state = frappe.db.get_value("Material Request", material_request, "workflow_state") or frappe.db.get_value("Material Request", material_request, "status")
        if state not in APPROVED:
            frappe.throw(_("Material Request {0} must be approved before issue.").format(material_request))

    for row in doc.items:
        quantity = abs(flt(row.qty))
        if row.material_request_item and not getattr(doc, "custom_return_against_stock_entry", None):
            allowed = flt(frappe.db.get_value("Material Request Item", row.material_request_item, "qty"))
            if issued(row.material_request_item, doc.name or "") + quantity > allowed + EPSILON:
                frappe.throw(_("Row {0} exceeds approved Material Request quantity.").format(row.idx))

        parent_stock_entry = getattr(doc, "custom_return_against_stock_entry", None)
        if parent_stock_entry:
            original = _original_detail(row, parent_stock_entry)
            if original.item_code != row.item_code:
                frappe.throw(_("Row {0}: return item must match the original Stock Entry Detail.").format(row.idx))
            prior = flt(frappe.db.sql("""
                select coalesce(sum(abs(sed.qty)), 0)
                from `tabStock Entry Detail` sed
                join `tabStock Entry` se on se.name = sed.parent
                where se.docstatus = 1
                  and se.custom_return_against_stock_entry = %s
                  and se.name != %s
                  and sed.custom_return_against_stock_entry_detail = %s
            """, (parent_stock_entry, doc.name or "", original.name))[0][0])
            if prior + quantity > abs(flt(original.qty)) + EPSILON:
                frappe.throw(_("Row {0}: return quantity exceeds the original issued quantity.").format(row.idx))
            if original.batch_no and getattr(row, "batch_no", None) != original.batch_no:
                frappe.throw(_("Row {0}: Batch Number must match the original issue.").format(row.idx))
            if original.serial_no and getattr(row, "serial_no", None) != original.serial_no:
                frappe.throw(_("Row {0}: Serial Numbers must match the original issue.").format(row.idx))


def update_material_request(doc, method=None):
    names = {getattr(doc, "custom_material_request", None)} if getattr(doc, "custom_material_request", None) else set()
    for row in doc.items:
        if row.material_request:
            names.add(row.material_request)
    for material_request in names:
        rows = frappe.get_all("Material Request Item", filters={"parent": material_request}, fields=["name", "qty"])
        values = [max(issued(row.name), 0) for row in rows]
        status = "Fully Issued" if rows and all(values[i] >= flt(rows[i].qty) - EPSILON for i in range(len(rows))) else "Partially Issued" if any(values) else "Not Issued"
        frappe.db.set_value("Material Request", material_request, "custom_issue_status", status, update_modified=False)


def _validate_activity(project, activity):
    if not activity:
        return
    if not frappe.db.exists("Workplan Activity", activity):
        frappe.throw(_("Activity Reference {0} does not exist.").format(activity))
    activity_project = frappe.db.get_value("Workplan Activity", activity, "project")
    if project and activity_project and activity_project != project:
        frappe.throw(_("Activity Reference must belong to Project {0}.").format(project))


def validate_material_request_activity(doc, method=None):
    if getattr(doc, "material_request_type", None) != "Material Issue":
        return
    _validate_activity(getattr(doc, "project", None), getattr(doc, "custom_activity_reference", None))
