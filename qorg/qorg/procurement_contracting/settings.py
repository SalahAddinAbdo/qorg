import frappe
from frappe import _
from qorg.qorg.enterprise_foundation.idempotent_provisioning import create_custom_fields_if_changed
from frappe.utils import cint, flt

PREFIX = "qorg_"

def _f(fieldname, label, fieldtype, insert_after, **kwargs):
    return {"fieldname": PREFIX + fieldname, "label": label, "fieldtype": fieldtype, "insert_after": insert_after, **kwargs}

FIELDS = {"Buying Settings": [
    _f("procurement_tab", "QOrg Procurement", "Tab Break", "document_naming_tab"),
    _f("controls_section", "Cycle Controls", "Section Break", "qorg_procurement_tab"),
    _f("enable_extended_procurement", "Enable Extended Procurement", "Check", "qorg_controls_section", default="1"),
    _f("enable_procurement_portal", "Enable Procurement Portal", "Check", "qorg_enable_extended_procurement", default="1"),
    _f("enable_supplier_registration", "Enable Supplier Registration", "Check", "qorg_enable_procurement_portal", default="1"),
    _f("enable_two_envelope", "Enable Two Envelope", "Check", "qorg_enable_supplier_registration", default="1"),
    _f("controls_column", "", "Column Break", "qorg_enable_two_envelope"),
    _f("enable_contract_management", "Enable Contract Management", "Check", "qorg_controls_column", default="1"),
    _f("require_receipt_before_goods_invoice", "Require Receipt Before Goods Invoice", "Check", "qorg_enable_contract_management", default="1"),
    _f("require_acceptance_before_service_invoice", "Require Acceptance Before Service Invoice", "Check", "qorg_require_receipt_before_goods_invoice", default="1"),
    _f("require_certification_before_works_invoice", "Require Certification Before Works Invoice", "Check", "qorg_require_acceptance_before_service_invoice", default="1"),
    _f("portal_section", "Supplier Portal", "Section Break", "qorg_require_certification_before_works_invoice"),
    _f("allow_supplier_profile_creation", "Allow Supplier Profile Creation", "Check", "qorg_portal_section", default="1"),
    _f("allow_supplier_profile_editing", "Allow Supplier Profile Editing", "Check", "qorg_allow_supplier_profile_creation", default="1"),
    _f("lock_profile_during_review", "Lock Profile During Review", "Check", "qorg_allow_supplier_profile_editing", default="1"),
    _f("lock_profile_after_approval", "Lock Profile After Approval", "Check", "qorg_lock_profile_during_review", default="1"),
    _f("portal_column", "", "Column Break", "qorg_lock_profile_after_approval"),
    _f("allow_update_request_after_approval", "Allow Update Request After Approval", "Check", "qorg_portal_column", default="1"),
    _f("lock_bank_information", "Lock Approved Bank Information", "Check", "qorg_allow_update_request_after_approval", default="1"),
    _f("profile_validity_days", "Profile Validity Days", "Int", "qorg_lock_bank_information", default="365"),
    _f("prevent_duplicate_submission", "Prevent Duplicate Submission", "Check", "qorg_profile_validity_days", default="1"),
    _f("enforce_submission_deadline", "Enforce Submission Deadline", "Check", "qorg_prevent_duplicate_submission", default="1"),
    _f("allow_submission_update_before_deadline", "Allow Submission Update Before Deadline", "Check", "qorg_enforce_submission_deadline", default="1"),
    _f("evaluation_section", "Submission and Evaluation Defaults", "Section Break", "qorg_allow_submission_update_before_deadline"),
    _f("default_two_envelope", "Two Envelope by Default", "Check", "qorg_evaluation_section", default="1"),
    _f("default_technical_weight", "Default Technical Weight", "Percent", "qorg_default_two_envelope", default="70"),
    _f("default_financial_weight", "Default Financial Weight", "Percent", "qorg_default_technical_weight", default="30"),
    _f("evaluation_column", "", "Column Break", "qorg_default_financial_weight"),
    _f("default_technical_threshold", "Default Technical Threshold", "Percent", "qorg_evaluation_column", default="70"),
    _f("allowed_file_types", "Allowed File Types", "Data", "qorg_default_technical_threshold", default="pdf,doc,docx,xls,xlsx,jpg,jpeg,png,zip"),
    _f("maximum_attachment_size_mb", "Maximum Attachment Size (MB)", "Int", "qorg_allowed_file_types", default="20"),
    _f("routing_section", "Default Responsibility Routing", "Section Break", "qorg_maximum_attachment_size_mb"),
    _f("default_procurement_officer", "Default Procurement Officer", "Link", "qorg_routing_section", options="User"),
    _f("default_logistics_officer", "Default Logistics Officer", "Link", "qorg_default_procurement_officer", options="User"),
    _f("default_stock_manager", "Default Stock Manager", "Link", "qorg_default_logistics_officer", options="User"),
    _f("routing_column", "", "Column Break", "qorg_default_stock_manager"),
    _f("default_contract_manager", "Default Contract Manager", "Link", "qorg_routing_column", options="User"),
    _f("default_acceptance_officer", "Default Acceptance Officer", "Link", "qorg_default_contract_manager", options="User"),
    _f("notifications_section", "Notifications and Alerts", "Section Break", "qorg_default_acceptance_officer"),
    _f("enable_procurement_notifications", "Enable Procurement Notifications", "Check", "qorg_notifications_section", default="1"),
    _f("submission_reminder_days", "Submission Reminder Days", "Int", "qorg_enable_procurement_notifications", default="3"),
    _f("contract_expiry_alert_days", "Contract Expiry Alert Days", "Int", "qorg_submission_reminder_days", default="30"),
    _f("notifications_column", "", "Column Break", "qorg_contract_expiry_alert_days"),
    _f("guarantee_expiry_alert_days", "Guarantee Expiry Alert Days", "Int", "qorg_notifications_column", default="30"),
    _f("notification_sender", "Notification Sender", "Link", "qorg_guarantee_expiry_alert_days", options="Email Account"),
    _f("default_cc_recipients", "Default CC Recipients", "Small Text", "qorg_notification_sender"),
]}

def provision_buying_settings_extension():
    create_custom_fields_if_changed(FIELDS, update=True)

def get_setting(fieldname, default=None):
    value = frappe.db.get_single_value("Buying Settings", PREFIX + fieldname)
    return default if value is None else value

def validate_buying_settings(doc, method=None):
    total = flt(doc.get("qorg_default_technical_weight")) + flt(doc.get("qorg_default_financial_weight"))
    if round(total, 6) != 100:
        frappe.throw(_("Technical and financial weights must total exactly 100%. Current total: {0}%; difference: {1}%.").format(total, 100 - total))
    if not 0 <= flt(doc.get("qorg_default_technical_threshold")) <= 100:
        frappe.throw(_("Technical threshold must be between 0 and 100."))
    if not 1 <= cint(doc.get("qorg_maximum_attachment_size_mb")) <= 100:
        frappe.throw(_("Maximum attachment size must be between 1 and 100 MB."))
    for fieldname in ("qorg_submission_reminder_days", "qorg_contract_expiry_alert_days", "qorg_guarantee_expiry_alert_days"):
        if cint(doc.get(fieldname)) < 0:
            frappe.throw(_("Alert and reminder days cannot be negative."))
