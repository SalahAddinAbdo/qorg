import frappe
from frappe import _
from frappe.utils import add_days, nowdate

LOCKED_STATUSES = {"Submitted", "Under Review", "Due Diligence", "Approved", "Suspended", "Expired"}
BANK_FIELDS = {"bank_name", "account_name", "account_number", "iban", "swift_code", "bank_currency", "bank_confirmation"}


def validate_supplier_registration(doc, method=None):
    settings = frappe.get_single("Procure Settings")
    old = None if doc.is_new() else frappe.get_doc(doc.doctype, doc.name)
    should_lock = (
        (settings.lock_profile_during_review and doc.registration_status in {"Submitted", "Under Review", "Due Diligence"})
        or (settings.lock_profile_after_approval and doc.registration_status == "Approved")
    )
    doc.profile_locked = int(bool(should_lock))
    if old and old.profile_locked and not doc.update_requested:
        changed = [f.fieldname for f in doc.meta.fields if doc.get(f.fieldname) != old.get(f.fieldname)]
        allowed = {"update_requested", "documents", "registration_status", "reviewer", "risk_rating", "review_expiry_date"}
        forbidden = [f for f in changed if f not in allowed]
        if forbidden:
            frappe.throw(_("Supplier profile is locked. Request an update before changing: {0}").format(", ".join(forbidden)))
    if old and settings.lock_bank_information and old.registration_status == "Approved":
        changed_bank = [f for f in BANK_FIELDS if doc.get(f) != old.get(f)]
        if changed_bank and not doc.update_requested:
            frappe.throw(_("Approved bank information requires a controlled update request."))
    if doc.registration_status == "Approved" and not doc.review_expiry_date:
        doc.review_expiry_date = add_days(nowdate(), settings.profile_validity_days or 365)


def create_or_link_supplier(doc, method=None):
    if doc.docstatus != 1 or doc.registration_status != "Approved" or doc.supplier:
        return
    existing = frappe.db.get_value("Supplier", {"supplier_name": doc.legal_name}, "name")
    if existing:
        doc.db_set("supplier", existing, update_modified=False)
        return
    supplier = frappe.get_doc({
        "doctype": "Supplier",
        "supplier_name": doc.legal_name,
        "supplier_type": doc.supplier_type or "Company",
        "country": doc.country,
        "tax_id": doc.tax_id,
    }).insert(ignore_permissions=True)
    doc.db_set("supplier", supplier.name, update_modified=False)
