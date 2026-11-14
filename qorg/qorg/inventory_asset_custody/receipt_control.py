from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt, getdate

CLOSED = {"Closed", "Cancelled", "Expired", "Terminated"}
EPSILON = 0.000001
ACCEPTING_RESULTS = {"Accepted", "Accepted with Minor Observations", "Partially Accepted"}


def _rejected_qty(row):
    return flt(getattr(row, "custom_rejected_qty", None) or getattr(row, "rejected_qty", None))


def _validated_inspection(row, receipt_name):
    if not row.quality_inspection:
        return None
    fields = ["name", "docstatus", "item_code"]
    meta = frappe.get_meta("Quality Inspection")
    fields.extend(x for x in ("custom_purchase_receipt", "custom_purchase_receipt_item", "custom_qorg_result", "custom_accepted_qty", "custom_rejected_qty") if meta.has_field(x))
    inspection = frappe.db.get_value("Quality Inspection", row.quality_inspection, fields, as_dict=True)
    if not inspection or inspection.docstatus != 1:
        frappe.throw(_("Row {0}: Quality Inspection must be submitted.").format(row.idx))
    if inspection.item_code and inspection.item_code != row.item_code:
        frappe.throw(_("Row {0}: Quality Inspection item does not match the receipt item.").format(row.idx))
    if inspection.get("custom_purchase_receipt") and receipt_name and inspection.custom_purchase_receipt != receipt_name:
        frappe.throw(_("Row {0}: Quality Inspection belongs to another Purchase Receipt.").format(row.idx))
    return inspection



def _validate_delivery(doc):
    method = getattr(doc, "custom_delivery_method", None)
    if not method:
        return
    if method in {"Third-Party Transporter", "Courier"} and not getattr(doc, "custom_transport_provider", None):
        frappe.throw(_("Transport Provider is required for the selected Delivery Method."))
    if method in {"Organization Vehicle", "Third-Party Transporter"} and not getattr(doc, "custom_vehicle_number", None):
        frappe.throw(_("Vehicle or Plate Number is required for the selected Delivery Method."))
    if getattr(doc, "custom_delivery_condition", None) and doc.custom_delivery_condition != "Good" and not getattr(doc, "custom_delivery_remarks", None):
        frappe.throw(_("Delivery Remarks are required when the delivery condition is not Good."))

def reconcile_receipt(doc, method=None):
    _validate_delivery(doc)
    settings = frappe.get_cached_doc("Stock Settings")
    tolerance = flt(settings.custom_over_receipt_tolerance) if getattr(settings, "custom_allow_over_receipt", 0) else 0
    contract = getattr(doc, "custom_procurement_contract", None)
    if contract:
        fields = [x for x in ("company", "status", "end_date", "extended_end_date") if frappe.get_meta("Procurement Contract").has_field(x)]
        contract_doc = frappe.db.get_value("Procurement Contract", contract, fields, as_dict=True) or {}
        if contract_doc.get("company") and contract_doc.company != doc.company:
            frappe.throw(_("Contract company must match receipt company."))
        if contract_doc.get("status") in CLOSED:
            frappe.throw(_("Receipt is not allowed against contract {0} with status {1}.").format(contract, contract_doc.status))
        expiry = contract_doc.get("extended_end_date") or contract_doc.get("end_date")
        if expiry and getdate(doc.posting_date) > getdate(expiry):
            frappe.throw(_("Contract {0} expired on {1}.").format(contract, expiry))

    accepted_total = rejected_total = 0
    for row in doc.items:
        current = abs(flt(row.qty))
        accepted = flt(getattr(row, "custom_accepted_qty", 0))
        rejected = _rejected_qty(row)
        if min(current, accepted, rejected) < -EPSILON:
            frappe.throw(_("Row {0}: quantities cannot be negative.").format(row.idx))
        if accepted + rejected > current + EPSILON:
            frappe.throw(_("Row {0}: accepted and rejected quantities exceed received quantity.").format(row.idx))

        ordered = flt(frappe.db.get_value("Purchase Order Item", row.purchase_order_item, "qty")) if row.purchase_order_item else 0
        prior_received = 0
        if row.purchase_order_item:
            prior_received = flt(frappe.db.sql("""
                select coalesce(sum(case when pr.is_return=0 then abs(pri.qty) else -abs(pri.qty) end),0)
                from `tabPurchase Receipt Item` pri
                join `tabPurchase Receipt` pr on pr.name=pri.parent
                where pr.docstatus=1 and pri.purchase_order_item=%s and pr.name!=%s
            """, (row.purchase_order_item, doc.name or ""))[0][0])
        if ordered and prior_received + current > ordered * (1 + tolerance / 100) + EPSILON:
            frappe.throw(_("Row {0} exceeds the allowed Purchase Order quantity.").format(row.idx))

        if getattr(doc, "custom_inspection_required", 0) and (accepted > EPSILON or rejected > EPSILON):
            inspection = _validated_inspection(row, doc.name)
            if not inspection:
                frappe.throw(_("Row {0}: submitted Quality Inspection is required before acceptance or rejection.").format(row.idx))
            result = inspection.get("custom_qorg_result")
            if accepted > flt(inspection.get("custom_accepted_qty")) + EPSILON:
                frappe.throw(_("Row {0}: accepted quantity exceeds the submitted Quality Inspection result.").format(row.idx))
            if rejected > flt(inspection.get("custom_rejected_qty")) + EPSILON:
                frappe.throw(_("Row {0}: rejected quantity exceeds the submitted Quality Inspection result.").format(row.idx))
            if accepted > EPSILON and result not in ACCEPTING_RESULTS:
                frappe.throw(_("Row {0}: Quality Inspection result does not allow acceptance.").format(row.idx))

        accepted_total += accepted
        rejected_total += rejected
        if hasattr(row, "custom_rejected_qty"):
            row.custom_rejected_qty = rejected

    if getattr(doc, "custom_inspection_required", 0) and not accepted_total and not rejected_total:
        doc.custom_receipt_acceptance_status = "Pending Inspection"
    elif rejected_total and accepted_total:
        doc.custom_receipt_acceptance_status = "Partially Accepted"
    elif rejected_total:
        doc.custom_receipt_acceptance_status = "Rejected"
    elif accepted_total:
        doc.custom_receipt_acceptance_status = "Accepted"
    else:
        doc.custom_receipt_acceptance_status = "Pending Acceptance"
