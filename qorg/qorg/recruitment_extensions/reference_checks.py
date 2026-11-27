from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint, now_datetime

from qorg.qorg.recruitment_extensions.settings import get_settings

OPEN_STATUSES = ("Draft", "Ready to Send", "Sent", "Follow-up Required", "Received")
ACCEPTABLE_RESULTS = ("Satisfactory", "Satisfactory with Reservations")


def _manager_permission():
    roles = set(frappe.get_roles())
    if frappe.session.user != "Administrator" and not roles.intersection({"Recruitment Manager", "HR Manager", "System Manager"}):
        frappe.throw(_("Recruitment Manager or HR Manager role is required."), frappe.PermissionError)


def _offer_status(offer):
    return frappe.db.get_value("Job Offer", offer, "qorg_response_status")


def _apply_links(doc):
    applicant = frappe.get_doc("Job Applicant", doc.job_applicant)
    doc.job_opening = applicant.get("qorg_job_opening")
    doc.external_person = applicant.get("qorg_external_person")
    doc.project = applicant.get("qorg_project")
    opening = frappe.get_doc("Job Opening", doc.job_opening) if doc.job_opening else None
    if opening:
        doc.company = opening.company
    if not doc.job_opening:
        frappe.throw(_("The Job Applicant must be linked to a Job Opening."))
    offer = frappe.get_doc("Job Offer", doc.job_offer)
    if offer.get("qorg_job_applicant") and offer.qorg_job_applicant != doc.job_applicant:
        frappe.throw(_("Job Offer does not belong to the selected Job Applicant."))


def validate_reference_check(doc):
    _manager_permission()
    _apply_links(doc)
    settings = get_settings()
    if settings.reference_check_trigger == "After Offer Acceptance" and _offer_status(doc.job_offer) != "Accepted":
        frappe.throw(_("Reference checks can start only after the candidate accepts the Job Offer."))
    if not (doc.email or doc.mobile_no):
        frappe.throw(_("Reference Email or Mobile Number is required."))
    duplicate = frappe.db.get_value(
        "Candidate Reference Check",
        {
            "job_offer": doc.job_offer,
            "reference_name": doc.reference_name,
            "email": doc.email or "",
            "status": ["not in", ["Cancelled"]],
            "name": ["!=", doc.name or ""],
        },
        "name",
    )
    if duplicate:
        frappe.throw(_("An active reference check already exists: {0}").format(duplicate))
    if doc.status not in ("Draft", "Ready to Send") and not doc.email:
        frappe.throw(_("Reference Email is required for sending and follow-up."))
    if doc.status == "Verified":
        if not doc.received_on or not doc.result or not doc.response_method:
            frappe.throw(_("Received On and Result are required before verification."))
        if settings.require_signed_reference_response and not doc.signed_response:
            frappe.throw(_("Signed Reference Response is required before verification."))
        if not doc.result_rationale:
            frappe.throw(_("Result Rationale is required before verification."))
        if not doc.verified_on:
            doc.verified_on = now_datetime()
            doc.verified_by = frappe.session.user
    if doc.result == "Unsatisfactory" and doc.status == "Verified" and not doc.result_rationale:
        frappe.throw(_("Result Rationale is required for an unsatisfactory result."))


def reference_check_summary(job_applicant):
    settings = get_settings()
    rows = frappe.get_all(
        "Candidate Reference Check",
        filters={"job_applicant": job_applicant, "status": ["!=", "Cancelled"]},
        fields=["status", "result"],
    )
    verified = [row for row in rows if row.status == "Verified"]
    unsatisfactory = [row for row in verified if row.result == "Unsatisfactory"]
    reservations = [row for row in verified if row.result == "Satisfactory with Reservations"]
    required = cint(settings.minimum_required_reference_checks) if settings.require_reference_checks else 0
    complete = len(verified) >= required and not unsatisfactory
    if reservations and not settings.allow_qualified_reference_result:
        complete = False
    return frappe._dict(
        required=required,
        total=len(rows),
        completed=len(verified),
        unsatisfactory=len(unsatisfactory),
        reservations=len(reservations),
        complete=complete,
    )


def update_applicant_reference_summary(job_applicant):
    if not job_applicant or not frappe.db.exists("Job Applicant", job_applicant):
        return
    summary = reference_check_summary(job_applicant)
    status = "Not Required" if not summary.required else "Completed" if summary.complete else "In Progress" if summary.total else "Not Started"
    frappe.db.set_value(
        "Job Applicant",
        job_applicant,
        {
            "qorg_reference_checks_required": summary.required,
            "qorg_reference_checks_completed": summary.completed,
            "qorg_reference_check_status": status,
            "qorg_latest_reference_check_on": now_datetime() if summary.completed else None,
        },
        update_modified=False,
    )


def validate_commencement_reference_checks(doc, method=None):
    settings = get_settings()
    if not settings.require_reference_checks or not settings.block_commencement_until_reference_checks:
        return
    applicant = doc.get("job_applicant")
    if not applicant and doc.get("job_offer"):
        applicant = frappe.db.get_value("Job Offer", doc.job_offer, "qorg_job_applicant")
    if not applicant:
        frappe.throw(_("Job Applicant is required to validate reference checks."))
    summary = reference_check_summary(applicant)
    if not summary.complete:
        frappe.throw(
            _("Reference checks are incomplete. Required: {0}; verified: {1}; unsatisfactory: {2}; reservations: {3}.").format(
                summary.required, summary.completed, summary.unsatisfactory, summary.reservations
            )
        )


def on_reference_check_update(doc, method=None):
    update_applicant_reference_summary(doc.job_applicant)


def on_reference_check_delete(doc, method=None):
    update_applicant_reference_summary(doc.job_applicant)


@frappe.whitelist(methods=["POST"])
def create_reference_checks_from_profile(job_applicant, job_offer):
    _manager_permission()
    if _offer_status(job_offer) != "Accepted":
        frappe.throw(_("The Job Offer must be accepted before creating reference checks."))
    applicant = frappe.get_doc("Job Applicant", job_applicant)
    if applicant.get("qorg_final_decision") != "Selected":
        frappe.throw(_("The Job Applicant must be selected."))
    person_name = applicant.get("qorg_external_person")
    if not person_name:
        frappe.throw(_("External Person is required."))
    person = frappe.get_doc("External Person", person_name)
    created = []
    for row in person.get("references") or []:
        exists = frappe.db.exists("Candidate Reference Check", {"job_offer": job_offer, "reference_source_row": row.name})
        if exists:
            continue
        check = frappe.get_doc({
            "doctype": "Candidate Reference Check",
            "job_applicant": job_applicant,
            "job_offer": job_offer,
            "reference_source_row": row.name,
            "reference_name": row.reference_name,
            "organization": row.organization,
            "designation": row.designation,
            "email": row.email,
            "mobile_no": row.mobile_no,
            "relationship": row.relationship,
            "status": "Ready to Send",
        })
        check.insert()
        created.append(check.name)
    if not created and not person.get("references"):
        frappe.throw(_("No professional references are available in the External Person profile."))
    update_applicant_reference_summary(job_applicant)
    return created


@frappe.whitelist(methods=["POST"])
def mark_reference_check_sent(name):
    _manager_permission()
    doc = frappe.get_doc("Candidate Reference Check", name)
    doc.status = "Sent"
    doc.sent_on = now_datetime()
    doc.requested_on = doc.requested_on or now_datetime()
    doc.requested_by = doc.requested_by or frappe.session.user
    doc.save()
    return doc.name


@frappe.whitelist(methods=["POST"])
def record_reference_check_received(name):
    _manager_permission()
    doc = frappe.get_doc("Candidate Reference Check", name)
    doc.status = "Received"
    doc.received_on = now_datetime()
    doc.save()
    return doc.name


@frappe.whitelist(methods=["POST"])
def verify_reference_check(name):
    _manager_permission()
    doc = frappe.get_doc("Candidate Reference Check", name)
    doc.status = "Verified"
    doc.save()
    return doc.name


def _reference_template():
    return frappe.get_doc("Email Template", "Recruitment - Candidate Reference Check Request - Bilingual")


def _questionnaire_pdf(doc):
    from frappe.utils.pdf import get_pdf
    template = frappe.get_template("qorg/qorg/recruitment_extensions/templates/candidate_reference_check_questionnaire.html")
    html = template.render({"doc": doc})
    return {"fname": f"{doc.name}-reference-check.pdf", "fcontent": get_pdf(html)}


@frappe.whitelist(methods=["POST"])
def send_reference_check_request(name):
    _manager_permission()
    doc = frappe.get_doc("Candidate Reference Check", name)
    if doc.status not in ("Draft", "Ready to Send", "Follow-up Required"):
        frappe.throw(_("The request can be sent only from Draft, Ready to Send, or Follow-up Required status."))
    if not doc.email:
        frappe.throw(_("Reference Email is required."))
    template = _reference_template()
    context = {"doc": doc}
    subject = frappe.render_template(template.subject, context)
    message = frappe.render_template(template.response_html or template.response, context)
    frappe.sendmail(
        recipients=[doc.email], subject=subject, message=message,
        attachments=[_questionnaire_pdf(doc)], reference_doctype=doc.doctype,
        reference_name=doc.name, now=True,
    )
    doc.status = "Sent"
    doc.sent_on = now_datetime()
    doc.requested_on = doc.requested_on or now_datetime()
    doc.requested_by = doc.requested_by or frappe.session.user
    doc.save()
    return doc.name


@frappe.whitelist(methods=["POST"])
def record_reference_check_follow_up(name):
    _manager_permission()
    doc = frappe.get_doc("Candidate Reference Check", name)
    if doc.status not in ("Sent", "Follow-up Required"):
        frappe.throw(_("Follow-up can be recorded only after the request is sent."))
    doc.status = "Follow-up Required"
    doc.reminder_count = cint(doc.reminder_count) + 1
    doc.last_reminder_on = now_datetime()
    doc.save()
    return doc.name
