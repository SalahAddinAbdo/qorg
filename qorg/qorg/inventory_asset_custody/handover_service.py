import frappe
from frappe import _
from frappe.utils import flt, getdate, now_datetime

EPSILON = 0.000001
DELIVERY_REQUIRED = {"Transfer", "External Delivery", "Partner Handover", "Beneficiary Distribution", "Field Location"}
VEHICLE_METHODS = {"Organization Vehicle", "Supplier Delivery", "Third-Party Transporter"}
PROVIDER_METHODS = {"Third-Party Transporter", "Courier"}


def populate_from_stock_entry(doc):
    if not doc.stock_entry or doc.items:
        return
    stock_entry = frappe.get_doc("Stock Entry", doc.stock_entry)
    if stock_entry.docstatus != 1:
        frappe.throw(_("Stock Entry must be submitted."))
    doc.company = stock_entry.company
    doc.material_request = getattr(stock_entry, "custom_material_request", None)
    doc.project = getattr(stock_entry, "project", None)
    doc.funding_source = getattr(stock_entry, "custom_funding_source", None)
    doc.workplan_activity = getattr(stock_entry, "custom_workplan_activity", None)
    doc.handed_over_by = frappe.session.user
    if doc.material_request and frappe.db.exists("Material Request", doc.material_request):
        request = frappe.db.get_value(
            "Material Request",
            doc.material_request,
            ["custom_issue_usage_type", "custom_issue_purpose", "custom_delivery_location", "custom_recipient_type", "custom_recipient_employee", "custom_return_expected", "custom_expected_return_date"],
            as_dict=True,
        ) or {}
        doc.issue_usage_type = request.get("custom_issue_usage_type")
        doc.issue_purpose = request.get("custom_issue_purpose")
        doc.destination_location = request.get("custom_delivery_location")
        doc.recipient_type = request.get("custom_recipient_type")
        doc.recipient_employee = request.get("custom_recipient_employee")
        doc.return_expected = request.get("custom_return_expected")
        doc.expected_return_date = request.get("custom_expected_return_date")
    for row in stock_entry.items:
        doc.append("items", {
            "stock_entry_detail": row.name,
            "item_code": row.item_code,
            "item_name": row.item_name,
            "uom": row.uom,
            "issued_qty": row.qty,
            "delivered_qty": row.qty,
            "received_qty": row.qty,
            "accepted_qty": row.qty,
            "batch_no": getattr(row, "batch_no", None),
            "serial_numbers": getattr(row, "serial_no", None),
        })


def _validate_recipient(doc):
    recipient_type = doc.recipient_type
    required_links = {
        "Employee": "recipient_employee",
        "External Person": "recipient_external_person",
        "Partner Organization": "recipient_partner",
        "Supplier": "recipient_supplier",
    }
    fieldname = required_links.get(recipient_type)
    if fieldname and not getattr(doc, fieldname, None):
        frappe.throw(_("{0} is required for Recipient Type {1}.").format(doc.meta.get_label(fieldname), recipient_type))
    if recipient_type != "Employee" and not doc.external_recipient_name:
        frappe.throw(_("External Recipient Name is required for the selected recipient type."))
    if recipient_type in {"Partner Organization", "Supplier"} and not doc.external_recipient_capacity:
        frappe.throw(_("Representative Capacity is required for the selected recipient type."))
    if recipient_type == "Employee":
        for fieldname in ("external_recipient_name", "external_recipient_email", "external_recipient_phone", "external_recipient_capacity", "external_recipient_id", "authorization_attachment"):
            setattr(doc, fieldname, None)
        doc.external_confirmation_method = None
        doc.recipient_signature = None


def _validate_usage(doc):
    if not doc.issue_usage_type:
        frappe.throw(_("Issue Usage Type is required."))
    if not doc.issue_purpose:
        frappe.throw(_("Issue Purpose is required."))
    if doc.issue_usage_type == "Beneficiary Distribution" and not doc.beneficiary_reference:
        frappe.throw(_("Beneficiary List or Distribution Reference is required."))
    if doc.issue_usage_type == "Partner Handover" and doc.recipient_type != "Partner Organization":
        frappe.throw(_("Partner Handover requires Recipient Type Partner Organization."))
    if doc.issue_usage_type == "Employee Custody" and doc.recipient_type != "Employee":
        frappe.throw(_("Employee Custody requires Recipient Type Employee."))
    if doc.issue_usage_type == "Temporary Issue":
        doc.return_expected = 1
    if doc.return_expected and not doc.expected_return_date:
        frappe.throw(_("Expected Return Date is required when a return is expected."))
    if doc.expected_return_date and getdate(doc.expected_return_date) < getdate(doc.posting_date):
        frappe.throw(_("Expected Return Date cannot be before the Handover Date."))


def _validate_delivery(doc):
    if doc.issue_usage_type in DELIVERY_REQUIRED and not doc.delivery_method:
        frappe.throw(_("Delivery Method is required for the selected Issue Usage Type."))
    if not doc.delivery_method:
        return
    if doc.delivery_method == "Recipient Pickup":
        doc.has_transporter = 0
    if not doc.destination_location:
        frappe.throw(_("Destination Location is required when Delivery Method is selected."))
    if doc.has_transporter:
        if not doc.transport_provider_type:
            frappe.throw(_("Transport Provider Type is required when a transporter is involved."))
        if doc.transport_provider_type == "Registered Transporter" and not doc.recipient_transporter:
            frappe.throw(_("Registered Transporter is required."))
        if doc.transport_provider_type in {"Courier", "Other"} and not doc.transport_provider:
            frappe.throw(_("External Transport Company is required."))
        if doc.transport_provider_type in {"Organization Fleet", "Registered Transporter"} and not doc.vehicle_number:
            frappe.throw(_("Vehicle or Plate Number is required."))
    else:
        for fieldname in ("transport_provider_type", "recipient_transporter", "transport_provider", "driver_name", "driver_phone", "vehicle_type", "vehicle_number", "waybill_number", "departure_datetime", "arrival_datetime", "transport_cost", "transport_cost_reference"):
            setattr(doc, fieldname, None)
    if doc.departure_datetime and doc.arrival_datetime and doc.arrival_datetime < doc.departure_datetime:
        frappe.throw(_("Arrival Date and Time cannot be before Departure Date and Time."))
    if doc.delivery_condition and doc.delivery_condition != "Good" and not doc.delivery_remarks:
        frappe.throw(_("Delivery Remarks are required when the delivery condition is not Good."))
    if flt(doc.transport_cost) < 0:
        frappe.throw(_("Transport Cost cannot be negative."))
    if flt(doc.transport_cost) > 0 and not doc.transport_cost_reference:
        frappe.throw(_("Transport Cost Reference is required when transport cost is entered."))


def validate_handover(doc):
    duplicate = frappe.db.exists("Stock Handover", {
        "stock_entry": doc.stock_entry,
        "name": ["!=", doc.name or ""],
        "docstatus": ["<", 2],
    })
    if duplicate:
        frappe.throw(_("Stock Entry already has handover {0}.").format(duplicate))

    _validate_recipient(doc)
    _validate_usage(doc)
    _validate_delivery(doc)
    if doc.workplan_activity and frappe.db.exists("DocType", "Project Workplan Activity"):
        activity_project = frappe.db.get_value("Project Workplan Activity", doc.workplan_activity, "project")
        if doc.project and activity_project and activity_project != doc.project:
            frappe.throw(_("Activity Reference must belong to Project {0}.").format(doc.project))

    difference = False
    for row in doc.items:
        issued = flt(row.issued_qty)
        delivered = flt(row.delivered_qty)
        received = flt(row.received_qty)
        rejected = flt(row.rejected_qty)
        damaged = flt(row.damaged_qty)
        short = max(delivered - received, 0)
        accepted = received - rejected - damaged
        if min(issued, delivered, received, rejected, damaged, accepted) < -EPSILON:
            frappe.throw(_("Row {0}: quantities cannot be negative or overlap.").format(row.idx))
        if delivered > issued + EPSILON or received > delivered + EPSILON:
            frappe.throw(_("Row {0}: delivered or received quantity is invalid.").format(row.idx))
        if abs((accepted + rejected + damaged + short) - delivered) > EPSILON:
            frappe.throw(_("Row {0}: accepted, rejected, damaged and short quantities must equal delivered quantity.").format(row.idx))
        row.accepted_qty = accepted
        row.short_qty = short
        if short > EPSILON:
            row.discrepancy_type = row.discrepancy_type or "Short"
        elif damaged > EPSILON:
            row.discrepancy_type = row.discrepancy_type or "Damaged"
        elif rejected > EPSILON:
            row.discrepancy_type = row.discrepancy_type or "Rejected"
        if (short > EPSILON or rejected > EPSILON or damaged > EPSILON) and not row.corrective_action:
            frappe.throw(_("Row {0}: Corrective Action is required for discrepancies.").format(row.idx))
        difference = bool(difference or short > EPSILON or rejected > EPSILON or damaged > EPSILON)

    if difference:
        doc.discrepancy_status = "Open"
        doc.fully_acknowledged = 0
        doc.handover_status = "Discrepancy Review"
    elif doc.docstatus == 1:
        doc.discrepancy_status = "None"
        doc.fully_acknowledged = 1
        doc.handover_status = "Acknowledged"
    else:
        doc.discrepancy_status = "None"
        doc.fully_acknowledged = 0
        doc.handover_status = "Pending Handover"


def mark_confirmation(doc):
    if doc.recipient_type != "Employee" and not doc.confirmation_datetime:
        doc.db_set("confirmation_datetime", now_datetime(), update_modified=False)
