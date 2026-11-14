from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt

EPSILON = 0.000001
ACTIONS = {
    "Accepted": "Release to Accepted Stock",
    "Accepted with Minor Observations": "Release to Accepted Stock",
    "Partially Accepted": "Hold in Quarantine",
    "Rejected": "Move to Rejected Stock",
    "Replacement Required": "Replacement Required",
    "Reinspection Required": "Reinspection Required",
}


def _positive(value, label):
    value = flt(value)
    if value < -EPSILON:
        frappe.throw(_("{0} cannot be negative.").format(label))
    return value


def _receipt_item(doc):
    if not getattr(doc, "custom_purchase_receipt", None):
        return None
    filters = {"parent": doc.custom_purchase_receipt}
    if getattr(doc, "item_code", None):
        filters["item_code"] = doc.item_code
    rows = frappe.get_all(
        "Purchase Receipt Item",
        filters=filters,
        fields=["name", "qty", "quality_inspection", "item_code", "batch_no", "serial_no"],
        order_by="idx asc",
        limit=2,
    )
    if getattr(doc, "custom_purchase_receipt_item", None):
        return frappe.db.get_value(
            "Purchase Receipt Item",
            doc.custom_purchase_receipt_item,
            ["name", "qty", "quality_inspection", "item_code", "batch_no", "serial_no"],
            as_dict=True,
        )
    if len(rows) == 1:
        return rows[0]
    return None


def validate_inspection(doc, method=None):
    inspected = _positive(doc.custom_inspected_qty, _("Inspected Quantity"))
    accepted = _positive(doc.custom_accepted_qty, _("Accepted Quantity"))
    rejected = _positive(doc.custom_rejected_qty, _("Rejected Quantity"))
    result = doc.custom_qorg_result

    if inspected <= EPSILON and result:
        frappe.throw(_("Inspected Quantity must be greater than zero before selecting a result."))
    if accepted + rejected > inspected + EPSILON:
        frappe.throw(_("Accepted and rejected quantities exceed inspected quantity."))
    if result and abs((accepted + rejected) - inspected) > EPSILON:
        frappe.throw(_("Accepted and rejected quantities must equal the inspected quantity. Current total: {0}; inspected: {1}.").format(accepted + rejected, inspected))

    if result in {"Accepted", "Accepted with Minor Observations"} and accepted <= EPSILON:
        frappe.throw(_("Accepted Quantity is required for the selected result."))
    if result == "Partially Accepted" and (accepted <= EPSILON or rejected <= EPSILON):
        frappe.throw(_("Partially Accepted requires both accepted and rejected quantities."))
    if result in {"Rejected", "Replacement Required"} and rejected <= EPSILON:
        frappe.throw(_("Rejected Quantity is required for the selected result."))
    if result == "Accepted with Minor Observations" and not getattr(doc, "custom_detailed_findings", None):
        frappe.throw(_("Inspection Findings are required for acceptance with minor observations."))
    if result == "Reinspection Required" and not getattr(doc, "custom_previous_quality_inspection", None):
        frappe.throw(_("Previous Quality Inspection is required for reinspection."))

    receipt_item = _receipt_item(doc)
    if receipt_item:
        if inspected > abs(flt(receipt_item.qty)) + EPSILON:
            frappe.throw(_("Inspected Quantity cannot exceed Purchase Receipt row quantity {0}.").format(abs(flt(receipt_item.qty))))
        if receipt_item.item_code and getattr(doc, "item_code", None) and receipt_item.item_code != doc.item_code:
            frappe.throw(_("Quality Inspection item must match the Purchase Receipt item."))

    doc.custom_release_action = ACTIONS.get(result, "Hold in Quarantine")


def _warehouse_setting(fieldname, label):
    warehouse = frappe.db.get_single_value("Stock Settings", fieldname)
    if not warehouse:
        frappe.throw(_("{0} is not configured in Stock Settings.").format(label))
    if not frappe.db.exists("Warehouse", warehouse):
        frappe.throw(_("Configured {0} does not exist.").format(label))
    if frappe.db.get_value("Warehouse", warehouse, "is_group"):
        frappe.throw(_("{0} must be a leaf warehouse.").format(label))
    if frappe.db.get_value("Warehouse", warehouse, "disabled"):
        frappe.throw(_("{0} is disabled.").format(label))
    return warehouse


def _ensure_create_permission(doctype):
    if not frappe.has_permission(doctype, "create"):
        frappe.throw(_("Not permitted to create {0}.").format(doctype), frappe.PermissionError)


def _inspection_context(doc):
    if doc.docstatus != 1:
        frappe.throw(_("Quality Inspection must be submitted."))
    if not doc.custom_purchase_receipt:
        frappe.throw(_("Purchase Receipt is required."))
    receipt = frappe.get_doc("Purchase Receipt", doc.custom_purchase_receipt)
    receipt.check_permission("read")
    if receipt.docstatus != 1:
        frappe.throw(_("Purchase Receipt must be submitted."))
    item = _receipt_item(doc)
    if not item:
        frappe.throw(_("Purchase Receipt Item is required or must be uniquely identifiable."))
    return receipt, item


def _copy_traceability(source, target_row):
    for fieldname in ("batch_no", "serial_no", "serial_and_batch_bundle"):
        value = source.get(fieldname) if hasattr(source, "get") else getattr(source, fieldname, None)
        if value and frappe.get_meta("Stock Entry Detail").has_field(fieldname):
            target_row.set(fieldname, value)


@frappe.whitelist()
def make_release_stock_entry(name):
    doc = frappe.get_doc("Quality Inspection", name)
    doc.check_permission("read")
    receipt, item = _inspection_context(doc)
    if getattr(doc, "custom_release_stock_entry", None):
        existing = frappe.get_doc("Stock Entry", doc.custom_release_stock_entry)
        existing.check_permission("read")
        return existing
    accepted = flt(doc.custom_accepted_qty)
    rejected = flt(doc.custom_rejected_qty)
    if accepted <= EPSILON and rejected <= EPSILON:
        frappe.throw(_("No accepted or rejected quantity is available for release."))
    source = _warehouse_setting("custom_quarantine_warehouse", _("Quarantine Warehouse"))
    accepted_warehouse = _warehouse_setting("custom_accepted_warehouse", _("Accepted Warehouse")) if accepted > EPSILON else None
    rejected_warehouse = _warehouse_setting("custom_rejected_warehouse", _("Rejected Warehouse")) if rejected > EPSILON else None
    _ensure_create_permission("Stock Entry")
    stock_entry = frappe.new_doc("Stock Entry")
    stock_entry.stock_entry_type = "Material Transfer"
    stock_entry.company = receipt.company
    stock_entry.posting_date = frappe.utils.nowdate()
    if frappe.get_meta("Stock Entry").has_field("custom_funding_source"):
        stock_entry.custom_funding_source = getattr(receipt, "custom_funding_source", None)
    stock_entry.custom_quality_inspection = doc.name
    for quantity, target in ((accepted, accepted_warehouse), (rejected, rejected_warehouse)):
        if quantity <= EPSILON:
            continue
        row = stock_entry.append("items", {
            "item_code": item.item_code,
            "qty": quantity,
            "s_warehouse": source,
            "t_warehouse": target,
            "uom": frappe.db.get_value("Item", item.item_code, "stock_uom"),
            "conversion_factor": 1,
            "project": getattr(receipt, "project", None),
        })
        _copy_traceability(item, row)
    return stock_entry


@frappe.whitelist()
def make_return_purchase_receipt(name):
    doc = frappe.get_doc("Quality Inspection", name)
    doc.check_permission("read")
    receipt, item = _inspection_context(doc)
    if flt(doc.custom_rejected_qty) <= EPSILON:
        frappe.throw(_("Rejected Quantity is required to create a return."))
    if getattr(doc, "custom_return_purchase_receipt", None):
        existing = frappe.get_doc("Purchase Receipt", doc.custom_return_purchase_receipt)
        existing.check_permission("read")
        return existing
    _ensure_create_permission("Purchase Receipt")
    returned = frappe.copy_doc(receipt)
    returned.name = None
    returned.docstatus = 0
    returned.is_return = 1
    returned.return_against = receipt.name
    returned.custom_quality_inspection = doc.name
    returned.set("items", [])
    new_row = returned.append("items", {})
    source_row = next((r for r in receipt.items if r.name == item.name), None)
    if not source_row:
        frappe.throw(_("Purchase Receipt Item was not found."))
    for fieldname in ("item_code", "item_name", "description", "uom", "stock_uom", "conversion_factor", "rate", "warehouse", "purchase_order", "purchase_order_item", "project", "cost_center", "expense_account", "batch_no", "serial_no", "serial_and_batch_bundle"):
        if hasattr(source_row, fieldname) and frappe.get_meta("Purchase Receipt Item").has_field(fieldname):
            new_row.set(fieldname, getattr(source_row, fieldname, None))
    new_row.qty = -abs(flt(doc.custom_rejected_qty))
    if frappe.get_meta("Purchase Receipt Item").has_field("custom_rejected_qty"):
        new_row.custom_rejected_qty = abs(flt(doc.custom_rejected_qty))
    return returned


@frappe.whitelist()
def mark_replacement_required(name):
    doc = frappe.get_doc("Quality Inspection", name)
    doc.check_permission("write")
    _inspection_context(doc)
    if doc.custom_qorg_result != "Replacement Required":
        frappe.throw(_("Inspection Result must be Replacement Required."))
    if getattr(doc, "custom_replacement_reference", None):
        return doc.custom_replacement_reference
    reference = "REPL-{0}".format(doc.name)
    doc.db_set("custom_replacement_reference", reference, update_modified=False)
    return reference


def validate_generated_stock_entry(doc, method=None):
    inspection_name = getattr(doc, "custom_quality_inspection", None)
    if not inspection_name:
        return
    inspection = frappe.get_doc("Quality Inspection", inspection_name)
    if inspection.docstatus != 1:
        frappe.throw(_("Linked Quality Inspection must be submitted."))
    if doc.purpose != "Material Transfer":
        frappe.throw(_("Quality release must use Material Transfer."))
    source = _warehouse_setting("custom_quarantine_warehouse", _("Quarantine Warehouse"))
    allowed_targets = {
        _warehouse_setting("custom_accepted_warehouse", _("Accepted Warehouse")),
        _warehouse_setting("custom_rejected_warehouse", _("Rejected Warehouse")),
    }
    for row in doc.items:
        if row.s_warehouse != source or row.t_warehouse not in allowed_targets:
            frappe.throw(_("Quality release rows must move from Quarantine Warehouse to Accepted or Rejected Warehouse."))
    existing = frappe.db.exists("Stock Entry", {
        "custom_quality_inspection": inspection_name,
        "docstatus": ["<", 2],
        "name": ["!=", doc.name or ""],
    })
    if existing:
        frappe.throw(_("Quality Inspection already has release Stock Entry {0}.").format(existing))


def register_release_stock_entry(doc, method=None):
    inspection_name = getattr(doc, "custom_quality_inspection", None)
    if inspection_name and doc.docstatus == 1:
        frappe.db.set_value("Quality Inspection", inspection_name, "custom_release_stock_entry", doc.name, update_modified=False)


def unregister_release_stock_entry(doc, method=None):
    inspection_name = getattr(doc, "custom_quality_inspection", None)
    if inspection_name and frappe.db.get_value("Quality Inspection", inspection_name, "custom_release_stock_entry") == doc.name:
        frappe.db.set_value("Quality Inspection", inspection_name, "custom_release_stock_entry", None, update_modified=False)


def validate_generated_return_receipt(doc, method=None):
    inspection_name = getattr(doc, "custom_quality_inspection", None)
    if not inspection_name:
        return
    inspection = frappe.get_doc("Quality Inspection", inspection_name)
    if inspection.docstatus != 1:
        frappe.throw(_("Linked Quality Inspection must be submitted."))
    if not doc.is_return or doc.return_against != inspection.custom_purchase_receipt:
        frappe.throw(_("Quality return must be a return against the inspected Purchase Receipt."))
    existing = frappe.db.exists("Purchase Receipt", {
        "custom_quality_inspection": inspection_name,
        "is_return": 1,
        "docstatus": ["<", 2],
        "name": ["!=", doc.name or ""],
    })
    if existing:
        frappe.throw(_("Quality Inspection already has return Purchase Receipt {0}.").format(existing))


def register_return_purchase_receipt(doc, method=None):
    inspection_name = getattr(doc, "custom_quality_inspection", None)
    if inspection_name and doc.docstatus == 1 and doc.is_return:
        frappe.db.set_value("Quality Inspection", inspection_name, "custom_return_purchase_receipt", doc.name, update_modified=False)


def unregister_return_purchase_receipt(doc, method=None):
    inspection_name = getattr(doc, "custom_quality_inspection", None)
    if inspection_name and frappe.db.get_value("Quality Inspection", inspection_name, "custom_return_purchase_receipt") == doc.name:
        frappe.db.set_value("Quality Inspection", inspection_name, "custom_return_purchase_receipt", None, update_modified=False)
