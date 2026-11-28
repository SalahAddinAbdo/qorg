from __future__ import annotations

import frappe

from qorg.qorg.enterprise_foundation.idempotent_provisioning import (
    create_custom_fields_if_changed,
)

# Runtime-only layout reconciliation for fields that are merged into Standard
# DocTypes after their JSON metadata is loaded. Existing business fields are
# updated only for layout/list properties. New records are layout breaks only.
LAYOUT_FIELDS = {
    "Budget Line": [
        {
            "fieldname": "qorg_budget_tree_section",
            "label": "Tree and Amendment Details",
            "fieldtype": "Section Break",
            "insert_after": "finance_values_overridden",
            "module": "QOrg",
            "is_system_generated": 1,
        },
    ],
    "External Opportunity": [
        {
            "fieldname": "qorg_publication_section",
            "label": "Website Publication",
            "fieldtype": "Section Break",
            "insert_after": "application_limit",
            "module": "QOrg",
            "is_system_generated": 1,
        },
        {"fieldname": "route", "insert_after": "qorg_publication_section"},
        {"fieldname": "published_by", "insert_after": "route"},
        {"fieldname": "portal_visibility", "insert_after": "published_by"},
        {"fieldname": "public_contact_email", "insert_after": "portal_visibility"},
    ],
    "Procurement Process": [
        {
            "fieldname": "qorg_responsibility_section",
            "label": "Workflow Responsibility",
            "fieldtype": "Section Break",
            "insert_after": "status",
            "module": "QOrg",
            "is_system_generated": 1,
        },
        {"fieldname": "custom_current_responsible_user", "insert_after": "qorg_responsibility_section"},
        {"fieldname": "custom_previous_responsible_user", "insert_after": "custom_current_responsible_user"},
    ],
    "Project Change Request": [
        {
            "fieldname": "qorg_budget_transfer_section",
            "label": "Budget Transfer Lines",
            "fieldtype": "Section Break",
            "insert_after": "donor_approval_reference",
            "module": "QOrg",
            "is_system_generated": 1,
        },
        {"fieldname": "budget_transfer_rows", "insert_after": "qorg_budget_transfer_section"},
        {
            "fieldname": "qorg_budget_transfer_audit_section",
            "label": "Budget Transfer Audit",
            "fieldtype": "Section Break",
            "insert_after": "budget_transfer_rows",
            "module": "QOrg",
            "is_system_generated": 1,
        },
        {"fieldname": "budget_transfer_applied_on", "insert_after": "qorg_budget_transfer_audit_section"},
        {"fieldname": "budget_transfer_applied_by", "insert_after": "budget_transfer_applied_on"},
        {"fieldname": "budget_transfer_audit", "insert_after": "budget_transfer_applied_by"},
        {
            "fieldname": "qorg_change_workflow_section",
            "label": "Workflow Responsibility",
            "fieldtype": "Section Break",
            "insert_after": "amended_from",
            "module": "QOrg",
            "is_system_generated": 1,
        },
        {"fieldname": "workflow_state", "insert_after": "qorg_change_workflow_section"},
        {"fieldname": "custom_current_responsible_user", "insert_after": "workflow_state"},
        {"fieldname": "custom_previous_responsible_user", "insert_after": "custom_current_responsible_user"},
    ],
    "Project Notification Rule": [
        {
            "fieldname": "qorg_rule_context_section",
            "label": "Rule Context",
            "fieldtype": "Section Break",
            "insert_after": "rule_label",
            "module": "QOrg",
            "is_system_generated": 1,
        },
        {"fieldname": "description", "insert_after": "qorg_rule_context_section"},
        {
            "fieldname": "qorg_rule_delivery_section",
            "label": "Trigger and Delivery",
            "fieldtype": "Section Break",
            "insert_after": "description",
            "module": "QOrg",
            "is_system_generated": 1,
        },
        {"fieldname": "reference_doctype", "insert_after": "qorg_rule_delivery_section", "columns": 2},
        {"fieldname": "trigger_type", "insert_after": "reference_doctype", "columns": 1},
        {"fieldname": "delivery_channel", "insert_after": "trigger_type", "in_list_view": 0},
        {
            "fieldname": "qorg_rule_recipients_section",
            "label": "Recipients and Template",
            "fieldtype": "Section Break",
            "insert_after": "delivery_channel",
            "module": "QOrg",
            "is_system_generated": 1,
        },
        {"fieldname": "recipient_users", "insert_after": "qorg_rule_recipients_section"},
        {"fieldname": "recipient_employees", "insert_after": "recipient_users"},
        {"fieldname": "fallback_to_project_manager", "insert_after": "recipient_employees"},
        {"fieldname": "notification_record", "insert_after": "fallback_to_project_manager"},
    ],
    "Service Allowance Accrual": [
        {
            "fieldname": "qorg_accrual_responsibility_section",
            "label": "Workflow Responsibility",
            "fieldtype": "Section Break",
            "insert_after": "workflow_state",
            "module": "QOrg",
            "is_system_generated": 1,
        },
        {"fieldname": "custom_current_responsible_user", "insert_after": "qorg_accrual_responsibility_section"},
        {"fieldname": "custom_previous_responsible_user", "insert_after": "custom_current_responsible_user"},
    ],
    "Shared Cost Allocation Run": [
        {
            "fieldname": "qorg_allocation_responsibility_section",
            "label": "Workflow Responsibility",
            "fieldtype": "Section Break",
            "insert_after": "run_status",
            "module": "QOrg",
            "is_system_generated": 1,
        },
        {"fieldname": "workflow_state", "insert_after": "qorg_allocation_responsibility_section"},
        {"fieldname": "custom_current_responsible_user", "insert_after": "workflow_state"},
        {"fieldname": "custom_previous_responsible_user", "insert_after": "custom_current_responsible_user"},
        {
            "fieldname": "qorg_rollback_section",
            "label": "Rollback Audit",
            "fieldtype": "Section Break",
            "insert_after": "reversal_journal_entry",
            "module": "QOrg",
            "is_system_generated": 1,
        },
        {"fieldname": "custom_rollback_method", "insert_after": "qorg_rollback_section"},
        {"fieldname": "custom_rollback_reason", "insert_after": "custom_rollback_method"},
        {"fieldname": "custom_rollback_by", "insert_after": "custom_rollback_reason"},
        {"fieldname": "custom_rollback_on", "insert_after": "custom_rollback_by"},
    ],
}

LAYOUT_PROPERTIES = ("insert_after", "in_list_view", "columns")


def _new_layout_breaks():
    definitions = {}
    for doctype, rows in LAYOUT_FIELDS.items():
        if not frappe.db.exists("DocType", doctype):
            continue
        for row in rows:
            if row.get("fieldtype") not in ("Section Break", "Column Break"):
                continue
            if not frappe.db.exists("Custom Field", f"{doctype}-{row['fieldname']}"):
                definitions.setdefault(doctype, []).append(row)
    return definitions


def _reconcile_existing_custom_fields():
    updated = []
    unchanged = []
    for doctype, rows in LAYOUT_FIELDS.items():
        for row in rows:
            name = f"{doctype}-{row['fieldname']}"
            if not frappe.db.exists("Custom Field", name):
                continue
            desired = {
                key: row[key]
                for key in LAYOUT_PROPERTIES
                if key in row
            }
            if not desired:
                continue
            current = frappe.db.get_value(
                "Custom Field", name, list(desired), as_dict=True
            ) or {}
            changes = {
                key: value
                for key, value in desired.items()
                if (current.get(key) or 0) != (value or 0)
            }
            if changes:
                frappe.db.set_value(
                    "Custom Field",
                    name,
                    changes,
                    update_modified=False,
                )
                updated.append(name)
            else:
                unchanged.append(name)
    return updated, unchanged


def reconcile_runtime_layouts():
    """Apply permanent, idempotent runtime layout reconciliation.

    Only missing layout breaks are created. Existing app-managed Custom Fields
    are updated solely for insert_after, in_list_view, and columns. Business
    types, options, validation, defaults, and stored data are never changed.
    """
    created = create_custom_fields_if_changed(_new_layout_breaks(), update=True)
    updated, unchanged = _reconcile_existing_custom_fields()
    frappe.clear_cache()
    return {
        "ok": True,
        "created": created,
        "updated": updated,
        "unchanged": unchanged,
    }


def audit_runtime_layouts():
    layout_types = {"Section Break", "Column Break", "Tab Break"}
    long_types = {"Text Editor", "Long Text", "Code", "HTML", "Table", "Table MultiSelect"}
    errors = []
    checked = 0
    child_tables = 0
    for doctype in frappe.get_all(
        "DocType",
        filters={"module": "QOrg", "custom": 0},
        pluck="name",
        order_by="name",
        limit_page_length=0,
    ):
        meta = frappe.get_meta(doctype, cached=False)
        fields = list(meta.fields)
        fieldnames = [field.fieldname for field in fields]
        if len(fieldnames) != len(set(fieldnames)):
            errors.append({"doctype": doctype, "issue": "Duplicate fieldname"})
        if meta.istable:
            child_tables += 1
            visible = [field for field in fields if field.in_list_view]
            width = sum(int(field.columns or 0) for field in visible)
            if len(visible) > 8:
                errors.append({"doctype": doctype, "issue": "Grid field count", "value": len(visible)})
            if width > 10:
                errors.append({"doctype": doctype, "issue": "Grid width", "value": width})
        starts = [i for i, field in enumerate(fields) if field.fieldtype in ("Section Break", "Tab Break")]
        if not starts or starts[0] > 0:
            starts = [0] + starts
        for start in dict.fromkeys(starts):
            end = len(fields)
            for index in range(start + 1, len(fields)):
                if fields[index].fieldtype in ("Section Break", "Tab Break"):
                    end = index
                    break
            count = sum(field.fieldtype not in layout_types for field in fields[start:end])
            if count > 9:
                errors.append({"doctype": doctype, "issue": "Dense section", "section": fields[start].fieldname, "value": count})
        for index, field in enumerate(fields):
            if field.fieldtype not in long_types:
                continue
            boundary = next(
                (
                    candidate
                    for candidate in fields[index + 1 :]
                    if candidate.fieldtype in ("Column Break", "Section Break", "Tab Break")
                ),
                None,
            )
            if boundary and boundary.fieldtype == "Column Break":
                errors.append({"doctype": doctype, "issue": "Long field in split column", "fieldname": field.fieldname})
        checked += 1
    return {
        "checked_doctypes": checked,
        "child_tables": child_tables,
        "error_count": len(errors),
        "errors": errors,
        "ok": not errors,
    }
