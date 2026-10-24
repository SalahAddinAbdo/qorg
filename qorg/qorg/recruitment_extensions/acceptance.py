import frappe

def audit_runtime_configuration():
    required_doctypes=["Recruitment Assessment Stage","Recruitment Notification Log","Work Commencement Notice"]
    required_templates=["Recruitment - Application Not Selected - Bilingual","Recruitment - Reserve Candidate - Bilingual","Recruitment - Work Commencement Internal Notice - Bilingual"]
    required_fields={"Interview":["qorg_job_opening","qorg_stage_sequence","qorg_attempt_number","qorg_previous_interview","qorg_allow_retry","qorg_maximum_attempts"],"Job Applicant":["qorg_overall_score","qorg_rank","qorg_last_notification_type"],"Job Opening":["qorg_assessment_plan"]}
    missing=[f"DocType: {x}" for x in required_doctypes if not frappe.db.exists("DocType",x)]
    missing += [f"Email Template: {x}" for x in required_templates if not frappe.db.exists("Email Template",x)]
    for dt,fields in required_fields.items():
        meta=frappe.get_meta(dt)
        missing += [f"Field: {dt}.{field}" for field in fields if not meta.has_field(field)]
    return {"ok":not missing,"missing":missing}
