from __future__ import annotations

import hashlib
import frappe
from frappe import _
from frappe.utils import add_months, flt, getdate, now_datetime, today

STANDARD_PARTIES = {"Customer", "Supplier", "Employee"}
TERMINAL_STATUSES = {"Expired", "Completed", "Terminated", "Cancelled", "Superseded"}


def _has(doc, fieldname):
    return doc.meta.has_field(fieldname)


def _set_if_blank(doc, fieldname, value):
    if value not in (None, "") and _has(doc, fieldname) and doc.get(fieldname) in (None, ""):
        doc.set(fieldname, value)


def _copy_table_if_empty(target, target_field, source, source_field):
    if not _has(target, target_field) or target.get(target_field) or not source or not source.get(source_field):
        return
    for row in source.get(source_field):
        values = {k: v for k, v in row.as_dict().items() if k not in {"name","parent","parenttype","parentfield","idx","doctype","creation","modified","modified_by","owner","docstatus"}}
        target.append(target_field, values)


def apply_defaults(doc, ctype, template=None):
    """Apply defaults once and only to blank fields: template, type, company, system."""
    if template:
        mapping = {
            "qorg_company":"qorg_company", "qorg_owning_department":"qorg_owning_department",
            "qorg_contract_manager":"qorg_contract_manager", "qorg_legal_owner":"qorg_legal_owner",
            "qorg_contract_purpose":"qorg_contract_purpose", "qorg_confidential":"qorg_confidential",
            "qorg_currency":"qorg_currency", "qorg_payment_basis":"qorg_payment_basis",
            "qorg_is_zero_value":"qorg_is_zero_value", "qorg_advance_payment_percent":"qorg_advance_payment_percent",
            "qorg_retention_percent":"qorg_retention_percent", "qorg_liquidated_damages_percent":"qorg_liquidated_damages_percent",
            "qorg_renewal_notice_days":"qorg_renewal_notice_days", "qorg_termination_notice_days":"qorg_termination_notice_days",
            "qorg_auto_renewal":"qorg_auto_renewal", "qorg_employment_type":"qorg_employment_type",
            "qorg_scope_of_work":"qorg_scope_of_work", "qorg_payment_terms":"qorg_payment_terms",
            "qorg_termination_terms":"qorg_termination_terms", "qorg_counterparty_doctype":"qorg_default_party_doctype",
        }
        for target, source in mapping.items():
            _set_if_blank(doc, target, template.get(source))
        if doc.is_new():
            for target, source in (("qorg_confidential","qorg_confidential"),("qorg_is_zero_value","qorg_is_zero_value"),("qorg_auto_renewal","qorg_auto_renewal")):
                if template.get(source) is not None:
                    doc.set(target, template.get(source))
        if not doc.end_date and doc.start_date and template.get("qorg_default_duration_months"):
            doc.end_date = add_months(doc.start_date, template.qorg_default_duration_months)
        if template.get("qorg_allow_open_ended") and not doc.end_date:
            doc.qorg_open_ended = 1
        for target_field in ("qorg_milestones","qorg_deliverables","qorg_guarantees","qorg_required_documents"):
            _copy_table_if_empty(doc, target_field, template, target_field)
    _set_if_blank(doc, "qorg_category", ctype.category)
    _set_if_blank(doc, "qorg_party_model", ctype.party_model)
    _set_if_blank(doc, "qorg_lifecycle_status", ctype.initial_lifecycle_status or "Draft")
    _set_if_blank(doc, "contract_template", ctype.default_contract_template)
    _set_if_blank(doc, "party_type", ctype.default_party_type)
    _set_if_blank(doc, "qorg_counterparty_doctype", ctype.default_extended_party_doctype)
    _set_if_blank(doc, "qorg_renewal_notice_days", ctype.renewal_notice_days)
    _set_if_blank(doc, "qorg_termination_notice_days", ctype.termination_notice_days)
    _set_if_blank(doc, "qorg_auto_renewal", ctype.auto_renewal_default)
    _set_if_blank(doc, "qorg_confidential", ctype.confidential_by_default)
    if not doc.end_date and doc.start_date and ctype.default_duration_months:
        doc.end_date = add_months(doc.start_date, ctype.default_duration_months)
    if ctype.allows_open_ended_period and not doc.end_date:
        doc.qorg_open_ended = 1
    if doc.qorg_company and not doc.qorg_currency and frappe.get_meta("Company").has_field("default_currency"):
        doc.qorg_currency = frappe.db.get_value("Company", doc.qorg_company, "default_currency")
    doc.qorg_default_values_applied = 1


def validate_contract(doc, method=None):
    if not _has(doc, "qorg_contract_type") or not doc.qorg_contract_type:
        return
    ctype = frappe.get_cached_doc("QOrg Contract Type", doc.qorg_contract_type)
    if not ctype.is_active:
        frappe.throw(_("Contract Type {0} is inactive.").format(ctype.name))
    # Resolve the type's default template before loading template defaults.
    if doc.is_new() and not doc.contract_template and ctype.default_contract_template:
        doc.contract_template = ctype.default_contract_template
    template = frappe.get_cached_doc("Contract Template", doc.contract_template) if doc.contract_template else None
    if template and template.get("qorg_contract_type") and template.qorg_contract_type != ctype.name:
        frappe.throw(_("Contract Template must belong to Contract Type {0}.").format(ctype.name))
    if doc.is_new() and not doc.qorg_default_values_applied:
        apply_defaults(doc, ctype, template)
    doc.qorg_category = ctype.category
    doc.qorg_party_model = ctype.party_model
    _validate_party(doc, ctype)
    _validate_dates(doc, ctype)
    _validate_required_context(doc, ctype)
    _validate_category_links(doc, ctype)
    _validate_overlap(doc)
    _track_template_snapshot(doc)
    _sync_standard_status(doc)


def _allowed_parties(ctype):
    return {(row.party_mode, row.party_doctype) for row in ctype.allowed_parties if row.is_active}


def _validate_party(doc, ctype):
    standard = bool(doc.party_type and doc.party_name)
    extended = bool(doc.qorg_counterparty_doctype and doc.qorg_counterparty)
    multiple = bool(doc.get("qorg_contract_parties"))
    model = ctype.party_model
    if model == "No Counterparty":
        if standard or extended or multiple:
            frappe.throw(_("This Contract Type does not allow a counterparty."))
        return
    allowed = _allowed_parties(ctype)
    if model == "Standard Party":
        if not standard or extended or multiple:
            frappe.throw(_("Specify one standard party for this contract."))
    elif model == "Extended Party":
        if not extended or standard or multiple:
            frappe.throw(_("Specify one extended party for this contract."))
    elif model == "Either Standard or Extended":
        if sum((standard, extended, multiple)) != 1 or multiple:
            frappe.throw(_("Specify either one standard party or one extended party."))
    elif model == "Multiple Parties":
        if not multiple or standard or extended:
            frappe.throw(_("Use the Contract Parties table for this multi-party contract."))
        primaries = [r for r in doc.qorg_contract_parties if r.is_primary]
        if ctype.require_primary_party and len(primaries) != 1:
            frappe.throw(_("Exactly one primary party is required."))
        seen = set()
        for row in doc.qorg_contract_parties:
            key = (row.party_mode, row.party_doctype, row.party)
            if key in seen:
                frappe.throw(_("Duplicate contract party {0}.").format(row.party))
            seen.add(key)
            if (row.party_mode, row.party_doctype) not in allowed:
                frappe.throw(_("Party type {0} is not allowed for this Contract Type.").format(row.party_doctype))
        return
    selected = ("Standard", doc.party_type) if standard else ("Extended", doc.qorg_counterparty_doctype)
    if selected not in allowed:
        frappe.throw(_("Party type {0} is not allowed for Contract Type {1}.").format(selected[1], ctype.name))
    if extended and doc.qorg_counterparty_doctype in STANDARD_PARTIES:
        frappe.throw(_("Use the standard party fields for {0}.").format(doc.qorg_counterparty_doctype))


def _validate_dates(doc, ctype):
    if doc.start_date and doc.end_date and getdate(doc.end_date) < getdate(doc.start_date):
        frappe.throw(_("Contract End Date cannot be before Start Date."))
    if doc.qorg_open_ended:
        if not ctype.allows_open_ended_period:
            frappe.throw(_("Open-ended periods are not allowed for Contract Type {0}.").format(ctype.name))
        doc.end_date = None
    elif not doc.end_date:
        frappe.throw(_("End Date is required unless Open-ended Contract is selected."))
    for fieldname in ("qorg_payroll_effective_date", "qorg_attendance_effective_date", "qorg_leave_effective_date"):
        value = doc.get(fieldname)
        if value and doc.start_date and getdate(value) < getdate(doc.start_date):
            frappe.throw(_("{0} cannot be before Contract Start Date.").format(doc.meta.get_label(fieldname)))
        if value and doc.end_date and getdate(value) > getdate(doc.end_date):
            frappe.throw(_("{0} cannot be after Contract End Date.").format(doc.meta.get_label(fieldname)))


def _require(doc, ctype, type_field, contract_field, label=None):
    if ctype.get(type_field) and not doc.get(contract_field):
        frappe.throw(_("{0} is required for Contract Type {1}.").format(label or doc.meta.get_label(contract_field), ctype.name))


def _validate_required_context(doc, ctype):
    if ctype.requires_value and (doc.qorg_is_zero_value or flt(doc.qorg_contract_value) <= 0):
        frappe.throw(_("A positive Contract Value is required."))
    if doc.qorg_is_zero_value and not ctype.allows_zero_value:
        frappe.throw(_("Zero-value contracts are not allowed for this Contract Type."))
    if doc.qorg_is_zero_value and flt(doc.qorg_contract_value):
        frappe.throw(_("A zero-value contract cannot have a Contract Value."))
    if doc.qorg_ceiling_amount and flt(doc.qorg_contract_value) > flt(doc.qorg_ceiling_amount):
        frappe.throw(_("Contract Value cannot exceed Ceiling Amount."))
    checks = [
        ("requires_currency","qorg_currency"),("requires_payment_basis","qorg_payment_basis"),
        ("requires_ceiling_amount","qorg_ceiling_amount"),("requires_project","qorg_project"),
        ("requires_cost_center","qorg_cost_center"),("requires_funding_agreement","qorg_funding_agreement"),
        ("requires_budget_line","qorg_budget_line"),("requires_procurement_source","qorg_procurement_process"),
        ("requires_award_decision","qorg_award_decision"),("requires_technical_manager","qorg_technical_manager"),
        ("requires_milestones","qorg_milestones"),("requires_deliverables","qorg_deliverables"),
        ("requires_guarantee","qorg_guarantees"),
    ]
    for type_field, contract_field in checks:
        _require(doc, ctype, type_field, contract_field)
    if ctype.requires_signed_document and doc.docstatus == 1 and not doc.qorg_contract_document:
        frappe.throw(_("Signed Contract Document is required before submission."))
    if ctype.requires_funding_context and not any((doc.qorg_project, doc.qorg_cost_center, doc.qorg_funding_agreement, doc.qorg_budget_line)):
        frappe.throw(_("A funding context is required."))


def _validate_category_links(doc, ctype):
    checks = [
        ("requires_employee","qorg_employee"),("requires_appointment_letter","qorg_appointment_letter"),
        ("requires_work_commencement","qorg_work_commencement_notice"),("requires_external_person","qorg_external_person"),
        ("requires_participation_engagement","qorg_participation_engagement"),("requires_supervisor","qorg_supervisor"),
        ("requires_expected_hours","qorg_expected_hours"),
    ]
    for type_field, contract_field in checks:
        _require(doc, ctype, type_field, contract_field)
    if doc.qorg_category == "Employment":
        employee = doc.qorg_employee or (doc.party_name if doc.party_type == "Employee" else None)
        if not employee:
            frappe.throw(_("Employee is required for an Employment contract."))
        if doc.party_type == "Employee" and doc.party_name != employee:
            frappe.throw(_("Party Name must match the linked Employee."))

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
    if doc.qorg_contract_type:
        ctype = frappe.get_cached_doc("QOrg Contract Type", doc.qorg_contract_type)
        if not ctype.is_active:
            frappe.throw(_("Contract Type {0} is inactive.").format(ctype.name))
        doc.qorg_category = ctype.category
        doc.qorg_party_model = ctype.party_model
        if doc.qorg_is_zero_value and not ctype.allows_zero_value:
            frappe.throw(_("This Contract Type does not allow zero-value templates."))
        if ctype.requires_currency and not doc.qorg_currency:
            frappe.throw(_("Default Currency is required by this Contract Type."))
        if ctype.requires_payment_basis and not doc.qorg_payment_basis:
            frappe.throw(_("Default Payment Basis is required by this Contract Type."))
        if ctype.requires_milestones and not doc.qorg_milestones:
            frappe.throw(_("Default Milestones are required by this Contract Type."))
        if ctype.requires_guarantee and not doc.qorg_guarantees:
            frappe.throw(_("Default Guarantees are required by this Contract Type."))
    if doc.qorg_legal_approval_status == "Approved":
        if not doc.qorg_contract_type:
            frappe.throw(_("Contract Type is required before approving a template."))
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
