from __future__ import annotations

import json
from collections import defaultdict

import frappe
from frappe import _
from frappe.utils import add_months, date_diff, getdate, now_datetime, today

RECORD = "Employee Document Record"
REQUIREMENT = "Employee Document Requirement"
DOC_TYPE = "Employee Document Type"
EXTERNAL_TYPES = {"External URL", "Microsoft SharePoint / OneDrive", "Google Drive", "External Document Management System"}
SENSITIVE = {"Highly Confidential", "Restricted HR", "Restricted Medical", "Restricted Financial", "Safeguarding Restricted"}


def validate_document_type(doc):
    days = []
    for token in (doc.expiry_warning_days or "").split(","):
        token = token.strip()
        if not token:
            continue
        try:
            value = int(token)
        except ValueError:
            frappe.throw(_("Expiry Warning Days must contain comma-separated whole numbers."))
        if value < 0:
            frappe.throw(_("Expiry Warning Days cannot be negative."))
        days.append(value)
    doc.expiry_warning_days = ",".join(str(x) for x in sorted(set(days), reverse=True))
    if doc.has_expiry_date and not doc.default_validity_months and doc.renewal_required:
        frappe.throw(_("Default Validity is required when renewal is mandatory."))


def validate_document_requirement(doc):
    if doc.effective_from and doc.effective_to and getdate(doc.effective_to) < getdate(doc.effective_from):
        frappe.throw(_("Effective To cannot be before Effective From."))
    if doc.warning_only:
        for fieldname in ("blocks_employment", "blocks_payroll", "blocks_attendance", "blocks_leave", "blocks_onboarding", "blocks_contract"):
            doc.set(fieldname, 0)
    if doc.requirement_level == "Recommended" and not doc.warning_only:
        doc.warning_only = 1
    if doc.required_before_payroll:
        doc.blocks_payroll = 1
    if doc.required_before_site_access:
        doc.blocks_attendance = 1
    if doc.required_before_contract_signature:
        doc.blocks_contract = 1


def validate_document_record(doc):
    if not frappe.db.exists(doc.subject_doctype, doc.subject_name):
        frappe.throw(_("Subject {0} {1} does not exist.").format(doc.subject_doctype, doc.subject_name))
    dtype = frappe.get_cached_doc(DOC_TYPE, doc.document_type)
    if not dtype.is_active:
        frappe.throw(_("Document Type {0} is inactive.").format(dtype.name))
    if dtype.applicable_subject_type not in {"Any Person", doc.subject_doctype}:
        frappe.throw(_("Document Type {0} does not apply to {1}.").format(dtype.name, doc.subject_doctype))
    doc.confidentiality_level = doc.confidentiality_level or dtype.confidentiality_level
    if dtype.reference_number_required and not doc.reference_number:
        frappe.throw(_("Reference Number is required."))
    if dtype.issuing_authority_required and not doc.issuing_authority:
        frappe.throw(_("Issuing Authority is required."))
    if dtype.has_issue_date and not doc.issue_date:
        frappe.throw(_("Issue Date is required."))
    if dtype.has_expiry_date and not doc.expiry_date:
        if doc.issue_date and dtype.default_validity_months:
            doc.expiry_date = add_months(doc.issue_date, dtype.default_validity_months)
        else:
            frappe.throw(_("Expiry Date is required."))
    if doc.issue_date and doc.expiry_date and getdate(doc.expiry_date) < getdate(doc.issue_date):
        frappe.throw(_("Expiry Date cannot be before Issue Date."))
    _validate_storage(doc, dtype)
    _validate_verification(doc, dtype)
    _validate_requirement_link(doc)
    _validate_active_uniqueness(doc, dtype)
    _derive_status(doc)


def _validate_storage(doc, dtype):
    storage = doc.storage_type
    if storage == "Frappe Attachment":
        if dtype.storage_reference_required and not doc.attachment:
            frappe.throw(_("Attachment is required."))
        if doc.attachment:
            file_name = frappe.db.get_value("File", {"file_url": doc.attachment}, "name")
            if file_name:
                doc.file_reference = file_name
                if doc.confidentiality_level in SENSITIVE:
                    is_private = frappe.db.get_value("File", file_name, "is_private")
                    if not is_private:
                        frappe.throw(_("Sensitive documents must use a private File."))
        doc.access_verification_status = "Not Applicable"
    elif storage == "Microsoft SharePoint / OneDrive":
        if not ((doc.microsoft_drive_id and doc.microsoft_item_id) or doc.external_url):
            frappe.throw(_("Microsoft Drive ID + Item ID, or an External URL, is required."))
    elif storage == "Google Drive":
        if not (doc.google_file_id or doc.external_url):
            frappe.throw(_("Google Drive File ID or External URL is required."))
    elif storage in {"External URL", "External Document Management System"}:
        if not (doc.external_document_id or doc.external_url):
            frappe.throw(_("External Document ID or URL is required."))
    elif storage == "Physical Document":
        if not doc.physical_location or not doc.archive_reference:
            frappe.throw(_("Physical Location and Archive Reference are required."))
        doc.access_verification_status = "Not Applicable"
    elif storage == "Reference Only":
        if not (doc.reference_number or doc.holding_organization):
            frappe.throw(_("Reference Number or Holding Organization is required."))
        doc.access_verification_status = "Not Applicable"
    else:
        frappe.throw(_("Unsupported Storage Type."))


def _validate_verification(doc, dtype):
    if doc.verification_status == "Verified":
        if not doc.verification_method:
            frappe.throw(_("Verification Method is required."))
        if not doc.verified_by:
            doc.verified_by = frappe.session.user
        if not doc.verified_on:
            doc.verified_on = now_datetime()
    if doc.verification_status == "Rejected" and not doc.rejection_reason:
        frappe.throw(_("Rejection Reason is required."))
    if doc.storage_type in EXTERNAL_TYPES and doc.access_verification_status == "Accessible":
        doc.last_access_verified_by = frappe.session.user
        doc.last_access_verified_on = now_datetime()
    if dtype.verification_required and doc.docstatus == 1 and doc.verification_status != "Verified":
        frappe.throw(_("Verification is required before submission."))


def _validate_requirement_link(doc):
    if not doc.requirement:
        return
    req = frappe.get_doc(REQUIREMENT, doc.requirement)
    if req.document_type != doc.document_type:
        frappe.throw(_("Requirement Document Type must match the record."))
    if not req.is_active:
        frappe.throw(_("The linked requirement is inactive."))


def _validate_active_uniqueness(doc, dtype):
    if dtype.multiple_active_records_allowed or doc.status in {"Superseded", "Revoked", "Rejected", "Expired"}:
        return
    other = frappe.db.get_value(RECORD, {"subject_doctype": doc.subject_doctype, "subject_name": doc.subject_name, "document_type": doc.document_type, "docstatus": ["<", 2], "status": ["not in", ["Superseded", "Revoked", "Rejected", "Expired"]], "name": ["!=", doc.name or ""]}, "name")
    if other:
        frappe.throw(_("Active document {0} already exists for this subject and type.").format(other))


def _derive_status(doc):
    if doc.expiry_date and getdate(doc.expiry_date) < getdate(today()) and doc.status not in {"Superseded", "Revoked"}:
        doc.status = "Expired"
    elif doc.verification_status == "Rejected":
        doc.status = "Rejected"
    elif doc.storage_type in EXTERNAL_TYPES and doc.access_verification_status in {"Access Denied", "Link Expired", "Document Missing", "Verification Failed"}:
        doc.status = "Access Failed"
    elif doc.verification_status == "Verified" and doc.status not in {"Superseded", "Revoked"}:
        doc.status = "Verified"
    elif doc.verification_status in {"Pending", "Not Verified"} and doc.status not in {"Draft", "Submitted"}:
        doc.status = "Pending Verification"


def submit_document_record(doc):
    if doc.supersedes_document:
        previous = frappe.get_doc(RECORD, doc.supersedes_document)
        if previous.subject_doctype != doc.subject_doctype or previous.subject_name != doc.subject_name or previous.document_type != doc.document_type:
            frappe.throw(_("Superseded document must belong to the same subject and document type."))
        frappe.db.set_value(RECORD, previous.name, {"status": "Superseded", "superseded_by": doc.name}, update_modified=False)
    _refresh_employee_readiness(doc)


def cancel_document_record(doc):
    if doc.supersedes_document and frappe.db.exists(RECORD, doc.supersedes_document):
        frappe.db.set_value(RECORD, doc.supersedes_document, {"status": "Verified", "superseded_by": None}, update_modified=False)
    _refresh_employee_readiness(doc)


def matching_requirements(subject_doctype, subject_name, on_date=None):
    on_date = getdate(on_date or today())
    subject = frappe.get_doc(subject_doctype, subject_name)
    context = _subject_context(subject_doctype, subject)
    candidates = frappe.get_all(REQUIREMENT, filters={"is_active": 1}, fields=["*"])
    matched = []
    for row in candidates:
        if row.effective_from and getdate(row.effective_from) > on_date:
            continue
        if row.effective_to and getdate(row.effective_to) < on_date:
            continue
        if _requirement_matches(row, context):
            row["specificity"] = _specificity(row)
            matched.append(row)
    # Merge same document type and preserve the strictest flags.
    merged = {}
    for row in sorted(matched, key=lambda x: x["specificity"]):
        current = merged.setdefault(row.document_type, frappe._dict(row))
        for flag in ("renewal_required", "verification_required", "valid_access_reference_required", "blocks_employment", "blocks_payroll", "blocks_attendance", "blocks_leave", "blocks_onboarding", "blocks_contract"):
            current[flag] = int(bool(current.get(flag) or row.get(flag)))
        if row.requirement_level == "Mandatory":
            current.requirement_level = "Mandatory"
        if row.specificity >= current.get("specificity", -1):
            current.name = row.name
            current.specificity = row.specificity
    return list(merged.values())


def document_compliance(subject_doctype, subject_name, on_date=None):
    requirements = matching_requirements(subject_doctype, subject_name, on_date)
    records = frappe.get_all(RECORD, filters={"subject_doctype": subject_doctype, "subject_name": subject_name, "docstatus": 1}, fields=["name", "document_type", "status", "expiry_date", "verification_status", "storage_type", "access_verification_status"], order_by="expiry_date desc")
    by_type = defaultdict(list)
    for row in records:
        by_type[row.document_type].append(row)
    results = []
    for req in requirements:
        valid = next((r for r in by_type.get(req.document_type, []) if _is_record_compliant(r, req, on_date)), None)
        results.append({"requirement": req.name, "document_type": req.document_type, "requirement_level": req.requirement_level, "compliant": bool(valid), "record": valid.name if valid else None, "blocks_employment": req.blocks_employment, "blocks_payroll": req.blocks_payroll, "blocks_attendance": req.blocks_attendance, "blocks_leave": req.blocks_leave, "warning_only": req.warning_only})
    return results


def document_service_blockers(employee_name, service, on_date=None):
    blockers, warnings, evidence = [], [], []
    for row in document_compliance("Employee", employee_name, on_date):
        if row["compliant"]:
            evidence.append(row["record"])
            continue
        message = _("Missing or non-compliant employee document: {0}").format(row["document_type"])
        blocks = row.get(f"blocks_{service}")
        if blocks and not row["warning_only"]:
            blockers.append(message)
        else:
            warnings.append(message)
    return blockers, warnings, evidence


def _is_record_compliant(record, requirement, on_date=None):
    on_date = getdate(on_date or today())
    if record.status != "Verified" or record.verification_status != "Verified":
        return False
    if record.expiry_date and getdate(record.expiry_date) < on_date:
        return False
    if requirement.valid_access_reference_required and record.storage_type in EXTERNAL_TYPES and record.access_verification_status != "Accessible":
        return False
    if record.status in {"Access Failed", "Expired", "Superseded", "Revoked", "Rejected"}:
        return False
    return True


def _subject_context(subject_doctype, subject):
    context = {"company": subject.get("company"), "branch": subject.get("branch"), "department": subject.get("department"), "designation": subject.get("designation"), "employee_grade": subject.get("grade") or subject.get("employee_grade"), "employment_type": subject.get("employment_type"), "project": subject.get("qorg_project") or subject.get("project")}
    if subject_doctype == "Employee":
        contract = frappe.db.get_value("Contract", {"qorg_employee": subject.name, "docstatus": ["<", 2]}, ["qorg_contract_type"], as_dict=True)
        context["contract_type"] = contract.qorg_contract_type if contract else None
    return context


def _requirement_matches(row, context):
    for fieldname in ("company", "branch", "department", "designation", "employee_grade", "employment_type", "contract_type", "project"):
        if row.get(fieldname) and row.get(fieldname) != context.get(fieldname):
            return False
    return True


def _specificity(row):
    weights = {"designation": 70, "employment_type": 60, "employee_grade": 50, "department": 40, "branch": 30, "company": 20, "contract_type": 65, "project": 55}
    return sum(weight for fieldname, weight in weights.items() if row.get(fieldname))


def update_document_statuses():
    if not frappe.db.exists("DocType", RECORD):
        return
    for row in frappe.get_all(RECORD, filters={"docstatus": 1, "status": ["not in", ["Superseded", "Revoked", "Rejected"]]}, fields=["name", "expiry_date", "status", "subject_doctype", "subject_name"]):
        if row.expiry_date and getdate(row.expiry_date) < getdate(today()) and row.status != "Expired":
            frappe.db.set_value(RECORD, row.name, "status", "Expired", update_modified=False)
            if row.subject_doctype == "Employee":
                _refresh_employee_readiness(frappe._dict(row))


def _refresh_employee_readiness(doc):
    if doc.subject_doctype != "Employee":
        return
    try:
        from qorg.qorg.employee_lifecycle.activation import evaluate_employee_readiness
        evaluate_employee_readiness(doc.subject_name, persist=True)
    except Exception:
        frappe.log_error(frappe.get_traceback(), f"Employee document readiness refresh failed: {doc.subject_name}")


def apply_document_readiness(result, employee_name):
    """Mutate a ReadinessResult with document blockers while preserving service independence."""
    for service, check in result.services.items():
        blockers, warnings, evidence = document_service_blockers(employee_name, service, check.effective_date)
        check.blockers.extend(x for x in blockers if x not in check.blockers)
        check.warnings.extend(x for x in warnings if x not in check.warnings)
        if evidence:
            check.evidence["employee_documents"] = evidence
        check.ready = not check.blockers
    return result


def evaluate_readiness_with_documents(employee_name, persist=True):
    from qorg.qorg.employee_lifecycle.activation import evaluate_employee_readiness, _persist_readiness
    employee = frappe.get_doc("Employee", employee_name)
    result = apply_document_readiness(evaluate_employee_readiness(employee_name, persist=False), employee_name)
    if persist:
        _persist_readiness(employee, result)
    return result
