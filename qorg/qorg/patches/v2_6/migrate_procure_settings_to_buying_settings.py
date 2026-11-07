import frappe
from qorg.qorg.procurement_contracting.settings import provision_buying_settings_extension

LEGACY_FIELDS = [
 "enable_extended_procurement","enable_procurement_portal","enable_supplier_registration","enable_two_envelope","enable_contract_management",
 "require_receipt_before_goods_invoice","require_acceptance_before_service_invoice","require_certification_before_works_invoice",
 "allow_supplier_profile_creation","allow_supplier_profile_editing","lock_profile_during_review","lock_profile_after_approval",
 "allow_update_request_after_approval","lock_bank_information","profile_validity_days","default_procurement_officer",
 "default_logistics_officer","default_stock_manager","default_contract_manager","default_acceptance_officer",
]

def execute():
    provision_buying_settings_extension()
    if not frappe.db.table_exists("tabProcure Settings"):
        return
    rows = frappe.db.sql("select * from `tabProcure Settings` limit 1", as_dict=True)
    if not rows:
        return
    legacy = rows[0]
    settings = frappe.get_single("Buying Settings")
    changed = False
    for fieldname in LEGACY_FIELDS:
        target = "qorg_" + fieldname
        if settings.meta.has_field(target) and legacy.get(fieldname) is not None:
            settings.set(target, legacy.get(fieldname))
            changed = True
    if changed:
        settings.flags.ignore_validate = True
        settings.save(ignore_permissions=True)
