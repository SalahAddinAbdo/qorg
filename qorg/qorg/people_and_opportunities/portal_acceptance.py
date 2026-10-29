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
    return {"ok": not missing, "missing": missing}
