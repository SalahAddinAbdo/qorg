from __future__ import annotations

import json
import os

import frappe
from frappe.model.document import get_controller


PROVISION = "qorg.qorg.volunteer_management.provisioning.provision_volunteer_management"

CORE_DOCTYPES = (
    "Participation Application",
    "Participation Assessment",
    "Participation Engagement",
    "Participation Service Log",
    "Participation Evaluation",
    "Participation Certificate",
)

CHILD_DOCTYPES = (
    "Participation Screening Criterion",
    "Participation Assessment Stage",
    "Participation Application Criterion",
    "Participation Onboarding Activity",
    "Participation Learning Objective",
    "Participation Allowance",
    "Participation Clearance Item",
)

HR_SETTINGS_FIELDS = (
    "qorg_participation_management_tab",
    "qorg_participation_default_type",
    "qorg_participation_minimum_age",
    "qorg_participation_require_agreement",
    "qorg_participation_require_code",
    "qorg_participation_require_safeguarding",
    "qorg_participation_block_pending_clearance",
    "qorg_participation_require_decision_rationale",
    "qorg_participation_max_daily_hours",
    "qorg_participation_max_weekly_hours",
    "qorg_participation_require_evidence",
    "qorg_participation_require_supervisor_verification",
    "qorg_participation_allow_overachievement",
    "qorg_participation_require_learning_objectives",
    "qorg_participation_require_midterm",
    "qorg_participation_require_final",
)

EXPECTED_HOOKS = {
    "External Opportunity.validate": (
        "qorg.qorg.volunteer_management.events.validate_external_opportunity",
    ),
    "Participation Application.validate": (
        "qorg.qorg.volunteer_management.cycle_integrity.validate_participation_record",
    ),
    "Participation Assessment.validate": (
        "qorg.qorg.volunteer_management.cycle_integrity.validate_participation_record",
    ),
    "Participation Engagement.validate": (
        "qorg.qorg.volunteer_management.cycle_integrity.validate_participation_record",
    ),
    "Participation Service Log.validate": (
        "qorg.qorg.volunteer_management.cycle_integrity.validate_participation_record",
    ),
    "Participation Evaluation.validate": (
        "qorg.qorg.volunteer_management.cycle_integrity.validate_participation_record",
    ),
    "Participation Certificate.validate": (
        "qorg.qorg.volunteer_management.cycle_integrity.validate_participation_record",
    ),
}

EXPECTED_CONTROLLER_METHODS = {
    "Participation Application": ("validate", "after_insert", "on_update", "on_trash"),
    "Participation Assessment": ("validate", "on_update", "after_delete"),
    "Participation Engagement": ("validate",),
    "Participation Service Log": ("validate", "on_update", "after_delete"),
    "Participation Evaluation": ("validate", "on_update"),
    "Participation Certificate": ("validate",),
}

LEGACY_DOCTYPES = (
    "Volunteer Profile",
    "Volunteer Application",
    "Volunteer Engagement",
)

WEB_FORMS = {
    "external-profile": {
        "doc_type": "External Person",
        "published": 1,
        "login_required": 1,
    },
    "participation-application": {
        "doc_type": "Participation Application",
        "published": 1,
        "login_required": 1,
    },
}


def _flatten(value):
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple)):
        return [item for value_item in value for item in _flatten(value_item)]
    return []


def _managed_template_names():
    folder = frappe.get_app_path(
        "qorg",
        "qorg",
        "volunteer_management",
        "data",
        "email_templates",
    )
    names = []
    if not os.path.isdir(folder):
        return names

    for filename in sorted(os.listdir(folder)):
        if not filename.endswith(".json"):
            continue
        with open(os.path.join(folder, filename), encoding="utf-8") as source:
            names.append(json.load(source)["name"])
    return names


def _audit_hooks(missing):
    hooks = frappe.get_hooks("doc_events") or {}
    for key, expected_paths in EXPECTED_HOOKS.items():
        doctype, event = key.split(".", 1)
        actual = _flatten((hooks.get(doctype) or {}).get(event))
        for path in expected_paths:
            if path not in actual:
                missing.append(f"Hook: {key} -> {path}")

    for doctype in CORE_DOCTYPES:
        actual = _flatten((hooks.get(doctype) or {}).get("on_trash"))
        expected = "qorg.qorg.volunteer_management.integrity.prevent_operational_delete"
        if expected not in actual:
            missing.append(f"Hook: {doctype}.on_trash -> {expected}")

    after_install = _flatten(frappe.get_hooks("after_install"))
    after_migrate = _flatten(frappe.get_hooks("after_migrate"))
    if PROVISION not in after_install:
        missing.append(f"Hook: after_install -> {PROVISION}")
    if PROVISION not in after_migrate:
        missing.append(f"Hook: after_migrate -> {PROVISION}")


def _audit_controllers(missing):
    for doctype, methods in EXPECTED_CONTROLLER_METHODS.items():
        try:
            controller = get_controller(doctype)
        except Exception as exc:
            missing.append(f"Controller: {doctype} ({exc})")
            continue

        for method in methods:
            if not callable(getattr(controller, method, None)):
                missing.append(f"Controller method: {doctype}.{method}")


def _audit_web_forms(missing):
    if not frappe.db.exists("DocType", "Web Form"):
        missing.append("DocType: Web Form")
        return

    for name, expected in WEB_FORMS.items():
        if not frappe.db.exists("Web Form", name):
            missing.append(f"Web Form: {name}")
            continue

        values = frappe.db.get_value(
            "Web Form",
            name,
            ["doc_type", "published", "login_required"],
            as_dict=True,
        )
        for fieldname, expected_value in expected.items():
            if values.get(fieldname) != expected_value:
                missing.append(
                    f"Web Form setting: {name}.{fieldname} = {expected_value}"
                )

    legacy_forms = frappe.get_all(
        "Web Form",
        filters={"doc_type": ["in", list(LEGACY_DOCTYPES)]},
        pluck="name",
    )
    for name in legacy_forms:
        missing.append(f"Legacy Web Form: {name}")


def _audit_permissions(missing):
    required_roles = ("Volunteer Coordinator", "Volunteer Manager")
    for role in required_roles:
        if not frappe.db.exists("Role", role):
            missing.append(f"Role: {role}")

    for doctype in CORE_DOCTYPES:
        meta = frappe.get_meta(doctype)
        roles = {permission.role for permission in meta.permissions}
        for role in required_roles:
            if role not in roles:
                missing.append(f"Permission: {doctype} -> {role}")

    engagement_meta = frappe.get_meta("Participation Engagement")
    submit_roles = {
        permission.role
        for permission in engagement_meta.permissions
        if permission.submit
    }
    if "Volunteer Manager" not in submit_roles:
        missing.append("Submit permission: Participation Engagement -> Volunteer Manager")


def audit_runtime_configuration():
    missing = []

    for doctype in CORE_DOCTYPES + CHILD_DOCTYPES:
        if not frappe.db.exists("DocType", doctype):
            missing.append(f"DocType: {doctype}")

    for doctype in LEGACY_DOCTYPES:
        if frappe.db.exists("DocType", doctype):
            missing.append(f"Legacy DocType still exists: {doctype}")

    if frappe.db.exists("Report", "Volunteer Application Pipeline"):
        missing.append("Legacy Report still exists: Volunteer Application Pipeline")

    for template in _managed_template_names():
        if not frappe.db.exists("Email Template", template):
            missing.append(f"Email Template: {template}")

    hr_settings = frappe.get_meta("HR Settings")
    for fieldname in HR_SETTINGS_FIELDS:
        if not hr_settings.has_field(fieldname):
            missing.append(f"Field: HR Settings.{fieldname}")

    _audit_hooks(missing)
    _audit_controllers(missing)
    _audit_web_forms(missing)
    _audit_permissions(missing)

    return {
        "ok": not missing,
        "missing": missing,
        "checked": {
            "core_doctypes": len(CORE_DOCTYPES),
            "child_doctypes": len(CHILD_DOCTYPES),
            "email_templates": len(_managed_template_names()),
            "hr_settings_fields": len(HR_SETTINGS_FIELDS),
            "web_forms": len(WEB_FORMS),
        },
    }
