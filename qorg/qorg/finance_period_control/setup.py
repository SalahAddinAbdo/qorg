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
        "Material Request": _material_request_route_fields(),
        "Purchase Order": _procurement_route_fields(),
        "Purchase Invoice": _procurement_route_fields(),
    }



def _procurement_route_fields():
    common = [
        {"fieldname":"procurement_route_section","label":"Procurement Route and Approval","fieldtype":"Section Break","insert_after":"procurement_control_tab"},
        {"fieldname":"qorg_procurement_method","label":"Approved Procurement Method","fieldtype":"Link","options":"Procurement Method","in_standard_filter":1,"read_only_depends_on":"eval:doc.qorg_route_inherited","insert_after":"procurement_route_section"},
        {"fieldname":"qorg_route_source","label":"Route Source","fieldtype":"Select","options":"Material Request\nProcurement Process\nAward Decision\nStandalone Document","read_only":1,"insert_after":"qorg_procurement_method"},
        {"fieldname":"qorg_route_inherited","label":"Route Inherited","fieldtype":"Check","read_only":1,"hidden":1,"insert_after":"qorg_route_source"},
        {"fieldname":"route_source_column","label":"","fieldtype":"Column Break","insert_after":"qorg_route_inherited"},
        {"fieldname":"qorg_procurement_process","label":"Procurement Process","fieldtype":"Link","options":"Procurement Process","read_only":1,"in_standard_filter":1,"insert_after":"route_source_column"},
        {"fieldname":"qorg_award_decision","label":"Award Decision","fieldtype":"Link","options":"Award Decision","read_only":1,"in_standard_filter":1,"insert_after":"qorg_procurement_process"},
        {"fieldname":"route_approval_section","label":"Exception Approval","fieldtype":"Section Break","insert_after":"qorg_award_decision"},
        {"fieldname":"qorg_route_approval_status","label":"Approval Status","fieldtype":"Select","options":"Not Required\nPending\nApproved\nRejected","read_only":1,"in_standard_filter":1,"insert_after":"route_approval_section"},
        {"fieldname":"qorg_route_reason","label":"Exception Reason","fieldtype":"Small Text","insert_after":"qorg_route_approval_status","read_only_depends_on":"eval:doc.qorg_route_inherited"},
        {"fieldname":"route_approval_column","label":"","fieldtype":"Column Break","insert_after":"qorg_route_reason"},
        {"fieldname":"qorg_route_approval_reference","label":"Approval Reference","fieldtype":"Data","insert_after":"route_approval_column","read_only_depends_on":"eval:doc.qorg_route_inherited"},
        {"fieldname":"qorg_route_approved_by","label":"Approved By","fieldtype":"Link","options":"User","read_only":1,"insert_after":"qorg_route_approval_reference"},
        {"fieldname":"qorg_route_approved_on","label":"Approved On","fieldtype":"Datetime","read_only":1,"insert_after":"qorg_route_approved_by"},
    ]
    return common


def _material_request_route_fields():
    return [
        {"fieldname":"procurement_planning_tab","label":"Procurement Planning","fieldtype":"Tab Break","insert_after":"terms_tab"},
        {"fieldname":"route_planning_section","label":"Procurement Route","fieldtype":"Section Break","insert_after":"procurement_planning_tab"},
        {"fieldname":"qorg_route_approval_status","label":"Route Approval Status","fieldtype":"Select","options":"Not Required\nPending\nApproved\nRejected","read_only":1,"in_standard_filter":1,"insert_after":"custom_procurement_method"},
        {"fieldname":"qorg_route_reason","label":"Exception Reason","fieldtype":"Small Text","insert_after":"qorg_route_approval_status"},
        {"fieldname":"route_planning_column","label":"","fieldtype":"Column Break","insert_after":"qorg_route_reason"},
        {"fieldname":"qorg_route_approval_reference","label":"Approval Reference","fieldtype":"Data","insert_after":"route_planning_column"},
        {"fieldname":"qorg_route_approved_by","label":"Approved By","fieldtype":"Link","options":"User","read_only":1,"insert_after":"qorg_route_approval_reference"},
        {"fieldname":"qorg_route_approved_on","label":"Approved On","fieldtype":"Datetime","read_only":1,"insert_after":"qorg_route_approved_by"},
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
    obsolete = {
        "Purchase Order": ("qorg_direct_procurement_section", "direct_procurement_section", "qorg_direct_procurement", "qorg_direct_procurement_reason", "qorg_direct_approval_reference"),
        "Purchase Invoice": ("qorg_direct_procurement_section", "direct_procurement_section", "qorg_direct_procurement", "qorg_direct_procurement_reason", "qorg_direct_approval_reference"),
    }
    for dt, fieldnames in obsolete.items():
        for fieldname in fieldnames:
            name = frappe.db.get_value("Custom Field", {"dt":dt,"fieldname":fieldname}, "name")
            if name:
                frappe.delete_doc("Custom Field", name, ignore_permissions=True, force=True)
    mr_positions = {
        "custom_procurement_policy_rule": "route_planning_section",
        "custom_procurement_method": "custom_procurement_policy_rule",
        "qorg_route_approval_status": "custom_procurement_method",
    }
    for fieldname, insert_after in mr_positions.items():
        name = frappe.db.get_value("Custom Field", {"dt":"Material Request","fieldname":fieldname}, "name")
        if name:
            frappe.db.set_value("Custom Field", name, "insert_after", insert_after, update_modified=False)
    for row in frappe.get_all("Custom Field", filters={"fieldtype":"Column Break"}, fields=["name","label"]):
        if row.label:
            frappe.db.set_value("Custom Field", row.name, "label", "", update_modified=False)


def execute():
    create_custom_fields(_layout_and_control_fields(), update=True)
    _compatibility_cleanup()
    ensure_finance_permissions()
    frappe.clear_cache()
