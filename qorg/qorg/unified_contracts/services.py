from __future__ import annotations

import hashlib
import frappe
from frappe import _
from frappe.utils import flt, getdate, now_datetime, today

STANDARD_PARTIES = {"Customer", "Supplier", "Employee"}
TERMINAL_STATUSES = {"Expired", "Completed", "Terminated", "Cancelled", "Superseded"}


def _has(doc, fieldname):
    return doc.meta.has_field(fieldname)


def validate_contract(doc, method=None):
    if not _has(doc, "qorg_contract_type") or not doc.qorg_contract_type:
        return
    ctype = frappe.get_cached_doc("QOrg Contract Type", doc.qorg_contract_type)
    if not ctype.is_active:
        frappe.throw(_("Contract Type {0} is inactive.").format(ctype.name))
    doc.qorg_category = ctype.category
    if not doc.contract_template and ctype.default_contract_template:
        doc.contract_template = ctype.default_contract_template
    if not doc.qorg_renewal_notice_days:
        doc.qorg_renewal_notice_days = ctype.renewal_notice_days
    if not doc.qorg_termination_notice_days:
        doc.qorg_termination_notice_days = ctype.termination_notice_days
    _validate_party(doc, ctype)
    _validate_dates(doc, ctype)
    _validate_required_context(doc, ctype)
    _validate_category_links(doc)
    _validate_overlap(doc)
    _track_template_snapshot(doc)
    _sync_standard_status(doc)


def _validate_party(doc, ctype):
    standard = bool(doc.party_type and doc.party_name)
    extended = bool(doc.qorg_counterparty_doctype and doc.qorg_counterparty)
    if standard == extended:
        frappe.throw(_("Specify exactly one legal counterparty: the standard party or the extended counterparty."))
    if standard:
        allowed = {x.strip() for x in (ctype.allowed_party_types or "").splitlines() if x.strip()}
        if allowed and doc.party_type not in allowed:
            frappe.throw(_("Party Type {0} is not allowed for Contract Type {1}.").format(doc.party_type, ctype.name))
    if extended and doc.qorg_counterparty_doctype in STANDARD_PARTIES:
        frappe.throw(_("Use the standard Party Type and Party Name fields for {0}.").format(doc.qorg_counterparty_doctype))


def _validate_dates(doc, ctype):
    if doc.start_date and doc.end_date and getdate(doc.end_date) < getdate(doc.start_date):
        frappe.throw(_("Contract End Date cannot be before Start Date."))
    if not doc.end_date and not ctype.allows_open_ended_period:
        frappe.throw(_("End Date is required for Contract Type {0}.").format(ctype.name))
    for fieldname in ("qorg_payroll_effective_date", "qorg_attendance_effective_date", "qorg_leave_effective_date"):
        value = doc.get(fieldname)
        if value and doc.start_date and getdate(value) < getdate(doc.start_date):
            frappe.throw(_("{0} cannot be before the Contract Start Date.").format(doc.meta.get_label(fieldname)))
        if value and doc.end_date and getdate(value) > getdate(doc.end_date):
            frappe.throw(_("{0} cannot be after the Contract End Date.").format(doc.meta.get_label(fieldname)))


def _validate_required_context(doc, ctype):
    if ctype.requires_value and not doc.qorg_is_zero_value and flt(doc.qorg_contract_value) <= 0:
        frappe.throw(_("Contract Value is required and must be greater than zero."))
    if doc.qorg_is_zero_value and flt(doc.qorg_contract_value):
        frappe.throw(_("A zero-value contract cannot have a Contract Value."))
    if doc.qorg_ceiling_amount and flt(doc.qorg_contract_value) > flt(doc.qorg_ceiling_amount):
        frappe.throw(_("Contract Value cannot exceed the Ceiling Amount."))
    if ctype.requires_funding_context and not (doc.qorg_project or doc.qorg_funding_agreement or doc.qorg_cost_center):
        frappe.throw(_("Project, Funding Agreement, or Cost Center is required for this Contract Type."))
    if ctype.requires_procurement_source and not (doc.qorg_procurement_process or doc.qorg_award_decision):
        frappe.throw(_("A procurement source is required for this Contract Type."))


def _validate_category_links(doc):
    if doc.qorg_category == "Employment":
        employee = doc.qorg_employee or (doc.party_name if doc.party_type == "Employee" else None)
        if not employee:
            frappe.throw(_("Employee is required for an Employment contract."))
        if doc.party_type == "Employee" and doc.party_name != employee:
            frappe.throw(_("Party Name must match the linked Employee."))
    elif doc.qorg_category in {"Volunteer", "Internship"}:
        if not (doc.qorg_external_person or doc.qorg_participation_engagement or doc.qorg_counterparty):
            frappe.throw(_("External Person, Participation Engagement, or Extended Party is required."))


def _validate_overlap(doc):
    if doc.qorg_lifecycle_status in TERMINAL_STATUSES or not doc.start_date:
        return
    identity = None
    if doc.party_type and doc.party_name:
        identity = {"party_type": doc.party_type, "party_name": doc.party_name}
    elif doc.qorg_counterparty_doctype and doc.qorg_counterparty:
        identity = {"qorg_counterparty_doctype": doc.qorg_counterparty_doctype, "qorg_counterparty": doc.qorg_counterparty}
    if not identity:
        return
    filters = {**identity, "qorg_contract_type": doc.qorg_contract_type, "name":["!=",doc.name or ""], "docstatus":["<",2], "qorg_lifecycle_status":["not in", list(TERMINAL_STATUSES)]}
    for row in frappe.get_all("Contract", filters=filters, fields=["name","start_date","end_date"]):
        row_start = getdate(row.start_date) if row.start_date else None
        row_end = getdate(row.end_date) if row.end_date else None
        this_start = getdate(doc.start_date)
        this_end = getdate(doc.end_date) if doc.end_date else None
        if row_start and (this_end is None or row_start <= this_end) and (row_end is None or this_start <= row_end):
            frappe.throw(_("Contract period overlaps with active Contract {0}.").format(row.name))


def _track_template_snapshot(doc):
    if not doc.contract_template or not doc.contract_terms:
        return
    current_hash = hashlib.sha256((doc.contract_terms or "").encode("utf-8")).hexdigest()
    if doc.is_new() or not doc.qorg_template_snapshot_hash or doc.has_value_changed("contract_template"):
        version = frappe.db.get_value("Contract Template", doc.contract_template, "qorg_version") or 1
        doc.qorg_template_version = version
        doc.qorg_template_snapshot_hash = current_hash
        doc.qorg_template_copied_on = now_datetime()
        doc.qorg_terms_modified_after_copy = 0
    elif doc.has_value_changed("contract_terms") and current_hash != doc.qorg_template_snapshot_hash:
        doc.qorg_terms_modified_after_copy = 1
        need_review = frappe.db.get_value("Contract Template", doc.contract_template, "qorg_changes_require_legal_review")
        if need_review and doc.qorg_lifecycle_status in {"Approved","Pending Signature","Active"}:
            frappe.throw(_("Contract terms differ from the approved template. Return the contract to review before saving."))


def _sync_standard_status(doc):
    lifecycle = doc.qorg_lifecycle_status
    if lifecycle in {"Active","Expiring"}:
        doc.status = "Active"
    elif lifecycle in TERMINAL_STATUSES or lifecycle == "Suspended":
        doc.status = "Inactive"
    else:
        doc.status = "Unsigned"


def validate_template(doc, method=None):
    if not _has(doc, "qorg_version"):
        return
    if doc.qorg_effective_from and doc.qorg_effective_to and getdate(doc.qorg_effective_to) < getdate(doc.qorg_effective_from):
        frappe.throw(_("Template Effective To cannot be before Effective From."))
    if doc.qorg_legal_approval_status == "Approved":
        if not doc.qorg_approved_by:
            doc.qorg_approved_by = frappe.session.user
        if not doc.qorg_approved_on:
            doc.qorg_approved_on = now_datetime()



def procurement_type_name(value):
    mapping = {"Goods Supply":"Goods Supply Contract","Service Contract":"Service Contract","Works Contract":"Works Contract","Consultancy Contract":"Consultancy Contract","Framework Agreement Call-off":"Framework Agreement"}
    return mapping.get(value, "Service Contract")


def validate_contract_amendment(doc, for_submit=False):
    contract = frappe.get_doc("Contract", doc.contract)
    if contract.docstatus == 2 or contract.qorg_lifecycle_status in {"Cancelled","Superseded"}:
        frappe.throw(_("A cancelled or superseded Contract cannot be amended."))
    if doc.is_new() or doc.has_value_changed("contract"):
        doc.old_start_date = contract.start_date
        doc.old_end_date = contract.end_date
        doc.currency = contract.qorg_currency
        doc.old_contract_value = contract.qorg_contract_value
    if doc.new_start_date and doc.new_end_date and getdate(doc.new_end_date) < getdate(doc.new_start_date):
        frappe.throw(_("New End Date cannot be before New Start Date."))
    if for_submit and not any([doc.new_start_date, doc.new_end_date, doc.new_contract_value is not None, doc.signed_amendment]):
        frappe.throw(_("Provide a structured change or attach the signed amendment before submission."))


def apply_contract_amendment(doc):
    contract = frappe.get_doc("Contract", doc.contract)
    values = {}
    if doc.new_start_date: values["start_date"] = doc.new_start_date
    if doc.new_end_date: values["end_date"] = doc.new_end_date
    if doc.new_contract_value is not None: values["qorg_contract_value"] = doc.new_contract_value
    if values:
        for key, value in values.items(): contract.set(key, value)
        contract.qorg_version_number = (contract.qorg_version_number or 1) + 1
        contract.flags.ignore_validate_update_after_submit = True
        contract.save(ignore_permissions=True)
    frappe.db.set_value("Contract Amendment", doc.name, {"status":"Applied","approved_by":frappe.session.user,"approved_on":now_datetime(),"applied_on":now_datetime()}, update_modified=False)


def update_expiring_contracts():
    if not frappe.db.exists("DocType", "Contract"):
        return
    for row in frappe.get_all("Contract", filters={"docstatus":["<",2],"qorg_lifecycle_status":["in",["Active","Expiring"]]}, fields=["name","end_date","qorg_renewal_notice_days"]):
        if not row.end_date: continue
        days = (getdate(row.end_date) - getdate(today())).days
        status = "Expired" if days < 0 else ("Expiring" if days <= (row.qorg_renewal_notice_days or 30) else "Active")
        frappe.db.set_value("Contract", row.name, "qorg_lifecycle_status", status, update_modified=False)
