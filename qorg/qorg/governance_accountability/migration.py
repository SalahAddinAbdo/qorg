from __future__ import annotations

import frappe
from frappe.utils import now_datetime

MIGRATION_VERSION = "procurement-complaint-v1.0"
STATUS_MAP = {
    "Received": "Received", "Under Review": "Under Review",
    "Additional Information Required": "Under Review",
    "Decision Issued": "Response Prepared", "Closed": "Closed",
}
TYPE_SUBJECT = {
    "Solicitation": "Procurement solicitation complaint",
    "Eligibility": "Procurement eligibility complaint",
    "Evaluation": "Procurement evaluation complaint",
    "Award": "Procurement award complaint",
    "Contracting": "Procurement contracting complaint",
    "Other": "Procurement complaint",
}


def _company_for_process(process):
    return frappe.db.get_value("Procurement Process", process, "company")


def migrate_procurement_complaints():
    if not frappe.db.exists("DocType", "Procurement Complaint") or not frappe.db.exists("DocType", "Accountability Case"):
        return {"ok": True, "skipped": True, "reason": "Required DocTypes are unavailable"}
    settings = frappe.get_single("Governance and Accountability Settings")
    if not settings.enable_legacy_procurement_complaint_migration:
        return {"ok": True, "skipped": True, "reason": "Migration is disabled in settings"}
    names = frappe.get_all("Procurement Complaint", pluck="name", order_by="creation asc")
    created, adopted, errors = [], [], []
    for name in names:
        existing = frappe.db.get_value("Accountability Case", {"legacy_doctype": "Procurement Complaint", "legacy_name": name})
        if existing:
            adopted.append(existing); continue
        savepoint = f"qorg_procurement_complaint_{len(created) + len(adopted)}"
        frappe.db.savepoint(savepoint)
        try:
            source = frappe.get_doc("Procurement Complaint", name)
            target = _make_case(source)
            target.flags.ignore_permissions = True
            target.flags.qorg_allow_legacy_migration = True
            target.insert(ignore_permissions=True)
            _move_files(source.name, target.name)
            created.append(target.name)
        except Exception:
            errors.append({"source": name, "error": frappe.get_traceback()})
            frappe.db.rollback(save_point=savepoint)
    return {"ok": not errors, "source_count": len(names), "created": created, "adopted": adopted, "errors": errors}


def _make_case(source):
    closed = source.status == "Closed"
    company = _company_for_process(source.procurement_process)
    reporter = frappe.db.get_value("Supplier", source.supplier, "supplier_name") if source.supplier else "Legacy Procurement Complainant"
    target = frappe.get_doc({
        "doctype": "Accountability Case",
        "case_type": "Complaint", "category": "Procurement", "channel": "Other",
        "received_on": source.received_on, "status": STATUS_MAP.get(source.status, "Under Review"),
        "priority": "Medium", "severity": "Medium", "confidentiality": "Restricted",
        "anonymous": 0, "stakeholder_type": "Supplier" if source.supplier else "Other",
        "reporter_name": reporter, "supplier": source.supplier,
        "company": company, "procurement_process": source.procurement_process,
        "related_doctype": "Procurement Process", "related_name": source.procurement_process,
        "subject": TYPE_SUBJECT.get(source.complaint_type, "Procurement complaint"),
        "case_details": source.complaint_details, "evidence": source.evidence,
        "custom_current_responsible_user": source.assigned_to,
        "review_summary": source.investigation_findings,
        "resolution_decision": source.decision or ("Legacy decision was not recorded" if closed else None),
        "corrective_action_summary": source.corrective_action,
        "closed_on": source.closed_on if closed else None,
        "closed_by": source.modified_by if closed else None,
        "closure_approved_by": source.modified_by if closed else None,
        "closure_rationale": "Migrated from closed Procurement Complaint" if closed else None,
        "legacy_doctype": "Procurement Complaint", "legacy_name": source.name,
        "external_tracking_enabled": 0,
        "migration_version": MIGRATION_VERSION, "migrated_on": now_datetime(),
    })
    if source.assigned_to:
        target.append("referrals", {
            "from_user": source.owner, "to_user": source.assigned_to,
            "to_role": "Procurement Manager", "referred_on": source.received_on,
            "status": "Accepted", "accepted_on": source.received_on,
            "referral_reason": "Migrated assignment from Procurement Complaint",
        })
    if source.decision:
        target.append("response_logs", {
            "response_on": source.closed_on or source.modified,
            "response_by": source.modified_by, "response_method": "Other",
            "response_summary": source.decision, "response_delivered": int(closed),
        })
    return target


def _move_files(source_name, target_name):
    rows = frappe.get_all("File", filters={"attached_to_doctype": "Procurement Complaint", "attached_to_name": source_name}, pluck="name")
    for file_name in rows:
        frappe.db.set_value("File", file_name, {
            "attached_to_doctype": "Accountability Case", "attached_to_name": target_name, "is_private": 1,
        }, update_modified=False)


def audit_procurement_migration():
    source = frappe.db.count("Procurement Complaint") if frappe.db.exists("DocType", "Procurement Complaint") else 0
    migrated = frappe.db.count("Accountability Case", {"legacy_doctype": "Procurement Complaint"}) if frappe.db.exists("DocType", "Accountability Case") else 0
    duplicate_rows = frappe.db.sql(
        """select legacy_name, count(*) as total from `tabAccountability Case`
           where legacy_doctype='Procurement Complaint' group by legacy_name having count(*) > 1""",
        as_dict=True,
    ) if frappe.db.exists("DocType", "Accountability Case") else []
    orphan_files = frappe.db.count("File", {"attached_to_doctype": "Procurement Complaint"})
    return {"ok": source == migrated and not duplicate_rows and not orphan_files,
            "source_count": source, "migrated_count": migrated,
            "duplicates": duplicate_rows, "legacy_attached_files": orphan_files}
