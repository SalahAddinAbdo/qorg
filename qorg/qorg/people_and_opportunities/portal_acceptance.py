import importlib

import frappe

REQUIRED_WEBSITE_FIELDS = (
    "qorg_opportunity_portal_enabled",
    "qorg_public_opportunity_listing",
    "qorg_external_applications_enabled",
    "qorg_default_opportunity_visibility",
    "qorg_show_upcoming_opportunities",
    "qorg_show_closed_opportunities",
    "qorg_opportunity_portal_page_size",
)


def audit_runtime_configuration():
    missing = []
    for doctype in ("External Opportunity", "External Person", "Website Settings", "Portal Settings"):
        if not frappe.db.exists("DocType", doctype):
            missing.append(f"DocType:{doctype}")
    metadata = frappe.get_meta("Website Settings")
    for fieldname in REQUIRED_WEBSITE_FIELDS:
        if not metadata.has_field(fieldname):
            missing.append(f"Website Settings.{fieldname}")
    for fieldname in ("route", "portal_visibility", "published_by"):
        if not frappe.get_meta("External Opportunity").has_field(fieldname):
            missing.append(f"External Opportunity.{fieldname}")
    if not frappe.db.exists("Role", "External Applicant"):
        missing.append("Role:External Applicant")
    for module_path in (
        "qorg.qorg.people_and_opportunities.portal_ownership",
        "qorg.qorg.people_and_opportunities.portal_permissions",
        "qorg.qorg.people_and_opportunities.private_files",
        "qorg.qorg.people_and_opportunities.identity",
        "qorg.qorg.people_and_opportunities.profile_completeness",
        "qorg.qorg.people_and_opportunities.web_form_request_security",
    ):
        try:
            importlib.import_module(module_path)
        except Exception as exc:
            missing.append(f"Import:{module_path} ({exc})")
    return {"ok": not missing, "missing": missing}


def _flatten_hook_values(value):
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple, set)):
        return [item for child in value for item in _flatten_hook_values(child)]
    return []


@frappe.whitelist()
def audit_deep_runtime_configuration():
    base = audit_runtime_configuration()
    missing = list(base.get("missing") or [])
    hooks = frappe.get_hooks()
    expected_permissions = {
        "External Person": "qorg.qorg.people_and_opportunities.portal_permissions.external_person_permission",
        "Participation Application": "qorg.qorg.people_and_opportunities.portal_permissions.participation_application_permission",
        "Job Applicant": "qorg.qorg.people_and_opportunities.portal_permissions.job_applicant_permission",
    }
    configured_permissions = hooks.get("has_permission") or {}
    for doctype, path in expected_permissions.items():
        actual = _flatten_hook_values(configured_permissions.get(doctype))
        if path not in actual:
            missing.append(f"Hook:has_permission:{doctype}")
    file_hooks = _flatten_hook_values(hooks.get("file_permission"))
    file_path = "qorg.qorg.people_and_opportunities.private_files.has_file_permission"
    if file_path not in file_hooks:
        missing.append("Hook:file_permission:people_and_opportunities")
    duplicates = frappe.db.sql(
        """select user, count(*) as total from `tabExternal Person`
           where ifnull(user, '') != '' group by user having count(*) > 1""",
        as_dict=True,
    )
    if duplicates:
        missing.append("Data:Duplicate External Person Users:" + ",".join(row.user for row in duplicates))
    public_files = frappe.db.sql(
        """select name from `tabFile`
           where attached_to_doctype in ('External Person','Participation Application','Job Applicant')
             and ifnull(is_private, 0) = 0 limit 20""",
        pluck=True,
    )
    if public_files:
        missing.append("Data:Public Protected Files:" + ",".join(public_files))
    return {"ok": not missing, "missing": missing}
