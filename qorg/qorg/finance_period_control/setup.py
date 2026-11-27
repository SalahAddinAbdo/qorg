import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from qorg.qorg.finance_period_control.permissions import ensure_finance_permissions


def _layout_and_control_fields():
    return {
        "Accounts Settings": [
            {"fieldname":"budget_control_tab","label":"Budget Control","fieldtype":"Tab Break","insert_after":"accounts_settings"},
            {"fieldname":"period_commitment_control_section","label":"Period and Commitment Control","fieldtype":"Section Break","insert_after":"budget_control_tab"},
            {"fieldname":"qorg_enable_period_budget_control","label":"Enable Period Budget Control","fieldtype":"Check","default":"0","insert_after":"period_commitment_control_section"},
            {"fieldname":"qorg_budget_period_basis","label":"Budget Period Basis","fieldtype":"Select","options":"Fiscal Year\nCalendar Month\nCustom Period","default":"Fiscal Year","insert_after":"qorg_enable_period_budget_control","depends_on":"eval:doc.qorg_enable_period_budget_control"},
            {"fieldname":"budget_control_column","label":"","fieldtype":"Column Break","insert_after":"qorg_budget_period_basis"},
            {"fieldname":"qorg_commitment_control_action","label":"Commitment Control Action","fieldtype":"Select","options":"Warn\nStop","default":"Stop","insert_after":"budget_control_column","depends_on":"eval:doc.qorg_enable_period_budget_control"},
        ],
        "Company": [
            {"fieldname":"budget_control_tab","label":"Budget Control","fieldtype":"Tab Break","insert_after":"default_settings"},
            {"fieldname":"default_control_settings_section","label":"Default Control Settings","fieldtype":"Section Break","insert_after":"budget_control_tab"},
            {"fieldname":"qorg_enable_period_budget_control","label":"Enable Period Budget Control","fieldtype":"Check","default":"0","insert_after":"default_control_settings_section"},
            {"fieldname":"qorg_default_budget_period","label":"Default Budget Period","fieldtype":"Link","options":"Budget Period","insert_after":"qorg_enable_period_budget_control","depends_on":"eval:doc.qorg_enable_period_budget_control"},
            {"fieldname":"budget_control_column","label":"","fieldtype":"Column Break","insert_after":"qorg_default_budget_period"},
            {"fieldname":"qorg_commitment_control_action","label":"Commitment Control Action","fieldtype":"Select","options":"Inherit Accounts Settings\nWarn\nStop","default":"Inherit Accounts Settings","insert_after":"budget_control_column","depends_on":"eval:doc.qorg_enable_period_budget_control"},
        ],
        "Project": [
            {"fieldname":"budget_funding_tab","label":"Budget and Funding","fieldtype":"Tab Break","insert_after":"project_details"},
            {"fieldname":"budget_control_section","label":"Budget Control","fieldtype":"Section Break","insert_after":"budget_funding_tab"},
            {"fieldname":"qorg_budget_control_policy","label":"Budget Control Policy","fieldtype":"Select","options":"Inherit Company\nWarn\nStop\nDisabled","default":"Inherit Company","insert_after":"budget_control_section"},
            {"fieldname":"budget_control_column","label":"","fieldtype":"Column Break","insert_after":"qorg_budget_control_policy"},
            {"fieldname":"qorg_default_budget_period","label":"Default Budget Period","fieldtype":"Link","options":"Budget Period","insert_after":"budget_control_column","depends_on":"eval:doc.qorg_budget_control_policy!='Disabled'"},
        ],
        "Budget": [
            {"fieldname":"synchronization_tab","label":"Synchronization","fieldtype":"Tab Break","insert_after":"accounts"},
            {"fieldname":"budget_synchronization_section","label":"Budget Synchronization","fieldtype":"Section Break","insert_after":"synchronization_tab"},
            {"fieldname":"qorg_managed_budget","label":"Managed Automatically","fieldtype":"Check","default":"0","read_only":1,"insert_after":"budget_synchronization_section"},
            {"fieldname":"sync_details_column","label":"","fieldtype":"Column Break","insert_after":"qorg_managed_budget"},
            {"fieldname":"qorg_sync_key","label":"Synchronization Key","fieldtype":"Data","read_only":1,"unique":1,"insert_after":"sync_details_column"},
            {"fieldname":"qorg_last_synced_on","label":"Last Synchronized On","fieldtype":"Datetime","read_only":1,"insert_after":"qorg_sync_key"},
        ],
        "Purchase Order": _direct_procurement_fields(),
        "Purchase Invoice": _direct_procurement_fields(),
    }


def _direct_procurement_fields():
    return [
        {"fieldname":"procurement_control_tab","label":"Procurement Control","fieldtype":"Tab Break","insert_after":"terms_tab"},
        {"fieldname":"direct_procurement_section","label":"Direct Procurement","fieldtype":"Section Break","insert_after":"procurement_control_tab"},
        {"fieldname":"qorg_direct_procurement","label":"Direct Procurement","fieldtype":"Check","default":"0","insert_after":"direct_procurement_section"},
        {"fieldname":"qorg_direct_procurement_reason","label":"Direct Procurement Reason","fieldtype":"Small Text","insert_after":"qorg_direct_procurement","mandatory_depends_on":"eval:doc.qorg_direct_procurement"},
        {"fieldname":"direct_procurement_column","label":"","fieldtype":"Column Break","insert_after":"qorg_direct_procurement_reason"},
        {"fieldname":"qorg_direct_approval_reference","label":"Approval Reference","fieldtype":"Data","insert_after":"direct_procurement_column","mandatory_depends_on":"eval:doc.qorg_direct_procurement"},
    ]


def _compatibility_cleanup():
    # Old layout sections are retained as records only so upgrades are nondestructive, but hidden.
    old_sections = {
        "Accounts Settings":"qorg_budget_control_section",
        "Company":"qorg_budget_control_section",
        "Project":"qorg_budget_control_section",
        "Budget":"qorg_sync_section",
        "Purchase Order":"qorg_direct_procurement_section",
        "Purchase Invoice":"qorg_direct_procurement_section",
    }
    for dt, fieldname in old_sections.items():
        name = frappe.db.get_value("Custom Field", {"dt":dt,"fieldname":fieldname}, "name")
        if name:
            frappe.db.set_value("Custom Field", name, {"hidden":1,"label":""}, update_modified=False)
    for row in frappe.get_all("Custom Field", filters={"fieldtype":"Column Break"}, fields=["name","label"]):
        if row.label:
            frappe.db.set_value("Custom Field", row.name, "label", "", update_modified=False)


def execute():
    create_custom_fields(_layout_and_control_fields(), update=True)
    _compatibility_cleanup()
    ensure_finance_permissions()
    frappe.clear_cache()
