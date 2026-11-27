import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    fields = {
        "Accounts Settings": [
            {"fieldname":"qorg_budget_control_section","label":"Multi-period Budget Control","fieldtype":"Section Break","insert_after":"allow_stale"},
            {"fieldname":"qorg_enable_period_budget_control","label":"Enable Period Budget Control","fieldtype":"Check","default":"0","insert_after":"qorg_budget_control_section"},
            {"fieldname":"qorg_budget_period_basis","label":"Budget Period Basis","fieldtype":"Select","options":"Fiscal Year\nCalendar Month\nCustom Period","default":"Fiscal Year","insert_after":"qorg_enable_period_budget_control","depends_on":"eval:doc.qorg_enable_period_budget_control"},
            {"fieldname":"qorg_commitment_control_action","label":"Commitment Control Action","fieldtype":"Select","options":"Warn\nStop","default":"Stop","insert_after":"qorg_budget_period_basis","depends_on":"eval:doc.qorg_enable_period_budget_control"},
        ],
        "Company": [
            {"fieldname":"qorg_budget_control_section","label":"Budget Control","fieldtype":"Section Break","insert_after":"default_currency"},
            {"fieldname":"qorg_enable_period_budget_control","label":"Enable Period Budget Control","fieldtype":"Check","insert_after":"qorg_budget_control_section"},
            {"fieldname":"qorg_default_budget_period","label":"Default Budget Period","fieldtype":"Link","options":"Budget Period","insert_after":"qorg_enable_period_budget_control","depends_on":"eval:doc.qorg_enable_period_budget_control"},
            {"fieldname":"qorg_commitment_control_action","label":"Commitment Control Action","fieldtype":"Select","options":"Inherit Accounts Settings\nWarn\nStop","default":"Inherit Accounts Settings","insert_after":"qorg_default_budget_period","depends_on":"eval:doc.qorg_enable_period_budget_control"},
        ],
        "Project": [
            {"fieldname":"qorg_budget_control_section","label":"Budget Control","fieldtype":"Section Break","insert_after":"company"},
            {"fieldname":"qorg_budget_control_policy","label":"Budget Control Policy","fieldtype":"Select","options":"Inherit Company\nWarn\nStop\nDisabled","default":"Inherit Company","insert_after":"qorg_budget_control_section"},
            {"fieldname":"qorg_default_budget_period","label":"Default Budget Period","fieldtype":"Link","options":"Budget Period","insert_after":"qorg_budget_control_policy"},
        ],
    }
    fields["Purchase Order"] = [
        {"fieldname":"qorg_direct_procurement_section","label":"Direct Procurement Control","fieldtype":"Section Break","insert_after":"project"},
        {"fieldname":"qorg_direct_procurement","label":"Direct Procurement","fieldtype":"Check","default":"0","insert_after":"qorg_direct_procurement_section"},
        {"fieldname":"qorg_direct_procurement_reason","label":"Direct Procurement Reason","fieldtype":"Small Text","insert_after":"qorg_direct_procurement","mandatory_depends_on":"eval:doc.qorg_direct_procurement"},
        {"fieldname":"qorg_direct_approval_reference","label":"Direct Approval Reference","fieldtype":"Data","insert_after":"qorg_direct_procurement_reason","mandatory_depends_on":"eval:doc.qorg_direct_procurement"},
    ]
    fields["Purchase Invoice"] = [
        {"fieldname":"qorg_direct_procurement_section","label":"Direct Procurement Control","fieldtype":"Section Break","insert_after":"project"},
        {"fieldname":"qorg_direct_procurement","label":"Direct Procurement","fieldtype":"Check","default":"0","insert_after":"qorg_direct_procurement_section"},
        {"fieldname":"qorg_direct_procurement_reason","label":"Direct Procurement Reason","fieldtype":"Small Text","insert_after":"qorg_direct_procurement","mandatory_depends_on":"eval:doc.qorg_direct_procurement"},
        {"fieldname":"qorg_direct_approval_reference","label":"Direct Approval Reference","fieldtype":"Data","insert_after":"qorg_direct_procurement_reason","mandatory_depends_on":"eval:doc.qorg_direct_procurement"},
    ]
    fields["Budget"] = [
        {"fieldname":"qorg_sync_section","label":"QOrg Budget Sync","fieldtype":"Section Break","insert_after":"fiscal_year"},
        {"fieldname":"qorg_managed_budget","label":"Managed by QOrg","fieldtype":"Check","default":"0","read_only":1,"insert_after":"qorg_sync_section"},
        {"fieldname":"qorg_sync_key","label":"QOrg Sync Key","fieldtype":"Data","unique":1,"read_only":1,"insert_after":"qorg_managed_budget"},
        {"fieldname":"qorg_last_synced_on","label":"QOrg Last Synced On","fieldtype":"Datetime","read_only":1,"insert_after":"qorg_sync_key"},
    ]
    create_custom_fields(fields, update=True)
    layout_breaks = {
        "Accounts Settings": [{"fieldname":"qorg_budget_control_column","fieldtype":"Column Break","insert_after":"qorg_budget_period_basis"}],
        "Company": [{"fieldname":"qorg_budget_control_column","fieldtype":"Column Break","insert_after":"qorg_enable_period_budget_control"}],
        "Project": [{"fieldname":"qorg_budget_control_column","fieldtype":"Column Break","insert_after":"qorg_budget_control_policy"}],
        "Budget": [{"fieldname":"qorg_sync_column","fieldtype":"Column Break","insert_after":"qorg_managed_budget"}],
        "Purchase Order": [{"fieldname":"qorg_direct_procurement_column","fieldtype":"Column Break","insert_after":"qorg_direct_procurement_reason"}],
        "Purchase Invoice": [{"fieldname":"qorg_direct_procurement_column","fieldtype":"Column Break","insert_after":"qorg_direct_procurement_reason"}],
    }
    create_custom_fields(layout_breaks, update=True)
    positions = {
        "Accounts Settings-qorg_commitment_control_action": "qorg_budget_control_column",
        "Company-qorg_default_budget_period": "qorg_budget_control_column",
        "Company-qorg_commitment_control_action": "qorg_default_budget_period",
        "Project-qorg_default_budget_period": "qorg_budget_control_column",
        "Budget-qorg_sync_key": "qorg_sync_column",
        "Budget-qorg_last_synced_on": "qorg_sync_key",
        "Purchase Order-qorg_direct_approval_reference": "qorg_direct_procurement_column",
        "Purchase Invoice-qorg_direct_approval_reference": "qorg_direct_procurement_column",
    }
    for name, insert_after in positions.items():
        if frappe.db.exists("Custom Field", name):
            frappe.db.set_value("Custom Field", name, "insert_after", insert_after, update_modified=False)
