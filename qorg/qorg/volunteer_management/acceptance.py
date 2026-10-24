import frappe

EXPECTED_HOOKS = {
    "External Opportunity.validate": "qorg.qorg.volunteer_management.events.validate_external_opportunity",
    "Participation Application.on_trash": "qorg.qorg.volunteer_management.integrity.prevent_operational_delete",
    "Participation Assessment.on_trash": "qorg.qorg.volunteer_management.integrity.prevent_operational_delete",
    "Participation Engagement.on_trash": "qorg.qorg.volunteer_management.integrity.prevent_operational_delete",
    "Participation Service Log.on_trash": "qorg.qorg.volunteer_management.integrity.prevent_operational_delete",
    "Participation Evaluation.on_trash": "qorg.qorg.volunteer_management.integrity.prevent_operational_delete",
    "Participation Certificate.on_trash": "qorg.qorg.volunteer_management.integrity.prevent_operational_delete",
}

def _flatten(value):
    if isinstance(value, str): return [value]
    if isinstance(value, (list, tuple)): return [x for item in value for x in _flatten(item)]
    return []

def audit_runtime_configuration():
    doctypes=["Participation Application","Participation Assessment","Participation Engagement","Participation Service Log","Participation Evaluation","Participation Certificate"]
    templates=["Participation - Application Received - Bilingual","Participation - Selection Notice - Bilingual","Participation - Application Not Selected - Bilingual","Participation - Certificate Issued - Bilingual"]
    missing=["DocType: "+x for x in doctypes if not frappe.db.exists("DocType",x)]
    missing += ["Email Template: "+x for x in templates if not frappe.db.exists("Email Template",x)]
    hr=frappe.get_meta("HR Settings")
    for field in ["qorg_participation_management_tab","qorg_participation_max_daily_hours","qorg_participation_require_final"]:
        if not hr.has_field(field): missing.append("Field: HR Settings."+field)
    hooks=frappe.get_hooks("doc_events") or {}
    for key,path in EXPECTED_HOOKS.items():
        doctype,event=key.split(".",1)
        actual=_flatten((hooks.get(doctype) or {}).get(event))
        if path not in actual: missing.append("Hook: "+key+" -> "+path)
    after_install=_flatten(frappe.get_hooks("after_install"))
    after_migrate=_flatten(frappe.get_hooks("after_migrate"))
    provision="qorg.qorg.volunteer_management.provisioning.provision_volunteer_management"
    if provision not in after_install: missing.append("Hook: after_install -> "+provision)
    if provision not in after_migrate: missing.append("Hook: after_migrate -> "+provision)
    return {"ok":not missing,"missing":missing}
