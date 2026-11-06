import frappe
from frappe import _
from frappe.utils import flt, getdate


def validate_contract(doc, method=None):
    calculate_contract_financials(doc)
    if doc.start_date and doc.end_date and getdate(doc.end_date) < getdate(doc.start_date):
        frappe.throw(_("Contract end date cannot precede the start date."))
    if flt(doc.ceiling_amount) and flt(doc.contract_value) > flt(doc.ceiling_amount):
        frappe.throw(_("Contract value cannot exceed the ceiling amount."))
    total_percent = sum(flt(r.percentage) for r in doc.milestones)
    if total_percent and abs(total_percent - 100) > 0.0001:
        frappe.throw(_("Contract milestone percentages must total exactly 100%. Current total: {0}%").format(total_percent))
    total_amount = sum(flt(r.amount) for r in doc.milestones)
    if total_amount and abs(total_amount - flt(doc.contract_value)) > 0.01:
        frappe.throw(_("Contract milestone amounts must equal the contract value."))


def validate_framework_call_off(doc, method=None):
    agreement = frappe.get_doc("Framework Agreement", doc.framework_agreement)
    if agreement.docstatus != 1 or agreement.status != "Active":
        frappe.throw(_("Framework Agreement must be submitted and active."))
    if getdate(doc.call_off_date) < getdate(agreement.valid_from) or getdate(doc.call_off_date) > getdate(agreement.valid_to):
        frappe.throw(_("Call-off date is outside the Framework Agreement validity period."))
    supplier_rows = {r.supplier: r for r in agreement.suppliers if r.active}
    if doc.supplier not in supplier_rows:
        frappe.throw(_("Supplier is not active in the selected Framework Agreement."))
    remaining = flt(agreement.total_ceiling) - flt(agreement.consumed_amount)
    if flt(doc.amount) > remaining:
        frappe.throw(_("Call-off amount exceeds the remaining agreement ceiling of {0}.").format(remaining))
    doc.validation_summary = _("Validated against agreement validity, supplier eligibility and remaining ceiling.")

def calculate_contract_financials(doc):
    doc.advance_payment_amount = flt(doc.contract_value) * flt(doc.advance_payment_percent) / 100
    doc.retention_amount = flt(doc.contract_value) * flt(doc.retention_percent) / 100
    doc.remaining_contract_value = flt(doc.contract_value) - flt(doc.invoiced_amount)
    if doc.remaining_contract_value < -0.01:
        frappe.throw(_("Invoiced amount cannot exceed the contract value."))


def validate_acceptance(doc, method=None):
    if flt(doc.completion_percent) < 0 or flt(doc.completion_percent) > 100:
        frappe.throw(_("Completion percentage must be between 0 and 100."))
    doc.eligible_invoice_amount = flt(doc.accepted_amount)
    doc.net_payable_amount = flt(doc.accepted_amount) - flt(doc.advance_recovery_amount) - flt(doc.retention_amount)
    if doc.net_payable_amount < 0:
        frappe.throw(_("Net payable amount cannot be negative."))
