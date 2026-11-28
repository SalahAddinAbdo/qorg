from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import add_days, getdate, now_datetime


def _score(value, label):
    value = int(value or 0)
    if value < 1 or value > 5:
        frappe.throw(_("{0} must be between 1 and 5.").format(label))
    return value


def validate_enterprise_risk(doc):
    for dt,name in (("Accountability Case",doc.accountability_case),("Assurance Finding",doc.assurance_finding)):
        if name:
            linked=frappe.get_doc(dt,name)
            if linked.company and linked.company!=doc.company:frappe.throw(_("Linked {0} belongs to another company.").format(dt))
    if doc.risk_owner and not frappe.db.exists("User", {"name": doc.risk_owner, "enabled": 1}):
        frappe.throw(_("Risk Owner must be an enabled user."))
    if doc.project_risk:
        project = frappe.db.get_value("Project Risk", doc.project_risk, "project")
        if project and doc.company:
            project_company = frappe.db.get_value("Project", project, "company")
            if project_company and project_company != doc.company:
                frappe.throw(_("Linked Project Risk belongs to another company."))
    latest = None
    for row in doc.assessments or []:
        row.likelihood = _score(row.likelihood, "Likelihood")
        row.impact = _score(row.impact, "Impact")
        row.residual_likelihood = _score(row.residual_likelihood, "Residual Likelihood")
        row.residual_impact = _score(row.residual_impact, "Residual Impact")
        row.inherent_score = row.likelihood * row.impact
        row.residual_score = row.residual_likelihood * row.residual_impact
        latest = row
    if latest:
        doc.last_reviewed_on = latest.assessment_on or now_datetime()
        doc.last_reviewed_by = latest.assessed_by or frappe.session.user
        threshold = int(doc.tolerance_threshold or 0)
        doc.escalation_required = int(bool(threshold and latest.residual_score > threshold))
        doc.priority = "Critical" if latest.residual_score >= 20 else "High" if latest.residual_score >= 12 else "Medium" if latest.residual_score >= 6 else "Low"
    old = doc.get_doc_before_save()
    if old and old.status == "Closed" and doc.status != "Closed":
        frappe.throw(_("Use the reopen action to reopen a closed Enterprise Risk."))
    if doc.status == "Closed":
        if not doc.assessments or not latest or latest.residual_score > int(doc.tolerance_threshold or 0):
            frappe.throw(_("Risk cannot close while residual exposure exceeds tolerance."))
        if not doc.closure_evidence or not doc.closure_notes:
            frappe.throw(_("Closure Evidence and Closure Notes are required."))
        if any(row.status not in ("Completed", "Cancelled") for row in doc.treatment_actions or []):
            frappe.throw(_("All treatment actions must be completed or cancelled before closure."))


def validate_compliance_obligation(doc):
    if doc.review_frequency_days is None or int(doc.review_frequency_days or 0) <= 0:
        frappe.throw(_("Review Frequency Days must be greater than zero."))
    if doc.effective_date and doc.expiry_date and getdate(doc.expiry_date) < getdate(doc.effective_date):
        frappe.throw(_("Expiry Date cannot precede Effective Date."))
    if doc.project and frappe.db.get_value("Project",doc.project,"company") not in (None,"",doc.company):frappe.throw(_("Project belongs to another company."))
    if doc.linked_risk and frappe.db.get_value("Enterprise Risk",doc.linked_risk,"company")!=doc.company:frappe.throw(_("Enterprise Risk belongs to another company."))
    if doc.corrective_action and frappe.db.get_value("Corrective Action",doc.corrective_action,"company")!=doc.company:frappe.throw(_("Corrective Action belongs to another company."))
    if doc.responsible_user and not frappe.db.exists("User", {"name": doc.responsible_user, "enabled": 1}):
        frappe.throw(_("Responsible User must be enabled."))
    latest = None
    for row in doc.reviews or []:
        if doc.evidence_required and row.status in ("Compliant", "Partially Compliant", "Noncompliant") and not row.evidence:
            frappe.throw(_("Evidence is required for assessed compliance reviews."))
        latest = row
    if latest:
        doc.current_compliance_status = latest.status
        doc.next_review_date = latest.next_review_date or add_days(latest.reviewed_on or now_datetime(), int(doc.review_frequency_days))
        if latest.status == "Noncompliant":
            doc.status = "Noncompliant"
            if not doc.corrective_action:
                frappe.throw(_("A Corrective Action is required for a noncompliant obligation."))
        elif doc.status in ("Draft", "Under Review", "Noncompliant"):
            doc.status = "Active"
    if doc.status == "Closed":
        if doc.current_compliance_status not in ("Compliant", "Not Applicable"):
            frappe.throw(_("Only compliant or not-applicable obligations can be closed."))
        if not doc.closure_evidence or not doc.closure_notes:
            frappe.throw(_("Closure Evidence and Closure Notes are required."))


def validate_assurance_finding(doc):
    if doc.source_name and not doc.source_doctype:
        frappe.throw(_("Source Document Type is required."))
    if doc.source_doctype and doc.source_name and not frappe.db.exists(doc.source_doctype, doc.source_name):
        frappe.throw(_("Source Document does not exist."))
    if doc.project and frappe.db.get_value("Project",doc.project,"company") not in (None,"",doc.company):frappe.throw(_("Project belongs to another company."))
    for dt,name in (("Corrective Action",doc.corrective_action),("Enterprise Risk",doc.enterprise_risk),("Compliance Obligation",doc.compliance_obligation)):
        if name and frappe.db.get_value(dt,name,"company")!=doc.company:frappe.throw(_("Linked {0} belongs to another company.").format(dt))
    if doc.classification in ("Major Nonconformity", "Critical Finding"):
        if not doc.responsible_user or not doc.due_date:
            frappe.throw(_("Responsible User and Due Date are required for major or critical findings."))
        if not doc.corrective_action:
            frappe.throw(_("Corrective Action is required for major or critical findings."))
    old = doc.get_doc_before_save()
    if old and old.status == "Closed" and doc.status != "Closed":
        frappe.throw(_("Closed findings cannot be reopened by direct status edit."))
    if doc.status == "Closed":
        if doc.effectiveness != "Effective" or not doc.verification_method or not doc.verification_evidence:
            frappe.throw(_("Effective verification with method and evidence is required before closure."))
        doc.verified_by = doc.verified_by or frappe.session.user
        doc.verified_on = doc.verified_on or now_datetime()
