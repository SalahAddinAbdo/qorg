import frappe

def audit_runtime_configuration():
    required_doctypes=["Recruitment Assessment Stage","Recruitment Notification Log","Work Commencement Notice","Candidate Reference Check"]
    required_templates=["Recruitment - Application Not Selected - Bilingual","Recruitment - Reserve Candidate - Bilingual","Recruitment - Work Commencement Internal Notice - Bilingual"]
    required_fields={"Interview":["qorg_job_opening","qorg_stage_sequence","qorg_attempt_number","qorg_previous_interview","qorg_allow_retry","qorg_maximum_attempts"],"Job Applicant":["qorg_overall_score","qorg_rank","qorg_last_notification_type","qorg_reference_checks_required","qorg_reference_checks_completed","qorg_reference_check_status"],"Job Opening":["qorg_assessment_plan"]}
    missing=[f"DocType: {x}" for x in required_doctypes if not frappe.db.exists("DocType",x)]
    missing += [f"Email Template: {x}" for x in required_templates if not frappe.db.exists("Email Template",x)]
    for dt,fields in required_fields.items():
        meta=frappe.get_meta(dt)
        missing += [f"Field: {dt}.{field}" for field in fields if not meta.has_field(field)]
    return {"ok":not missing,"missing":missing}


def audit_deep_runtime_configuration():
    base = audit_runtime_configuration()
    missing = list(base.get("missing") or [])
    required_settings = (
        "qorg_require_reference_checks", "qorg_reference_check_trigger",
        "qorg_minimum_required_reference_checks", "qorg_require_signed_reference_response",
        "qorg_block_commencement_until_reference_checks", "qorg_allow_qualified_reference_result",
    )
    meta = frappe.get_meta("HR Settings")
    missing += [f"Field: HR Settings.{field}" for field in required_settings if not meta.has_field(field)]
    for module in (
        "qorg.qorg.recruitment_extensions.reference_checks",
        "qorg.qorg.doctype.candidate_reference_check.candidate_reference_check",
    ):
        try:
            __import__(module)
        except Exception as exc:
            missing.append(f"Import: {module} ({exc})")
    if not frappe.db.exists("Email Template", "Recruitment - Candidate Reference Check Request - Bilingual"):
        missing.append("Email Template: Recruitment - Candidate Reference Check Request - Bilingual")
    return {"ok": not missing, "missing": missing}
