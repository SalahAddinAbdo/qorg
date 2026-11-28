from __future__ import annotations
import frappe
from frappe import _
from frappe.utils import add_days, get_datetime, now_datetime
from qorg.qorg.governance_accountability.settings import get_settings
CLOSED_STATUSES={"Closed","Withdrawn","Duplicate","Out of Scope","Referred Externally"}
SENSITIVE_LEVELS={"Confidential","Highly Confidential"}

def validate_accountability_case(doc):
    settings=get_settings();legacy=bool(getattr(doc.flags,"qorg_allow_legacy_migration",False));doc.received_on=doc.received_on or now_datetime()
    _validate_classification(doc,settings);_validate_reporter(doc,settings);_validate_context(doc);_validate_links(doc);_protect_sensitive_changes(doc)
    if not legacy:_validate_status(doc)
    _apply_initial_sla(doc,settings)
    doc.overdue=int(bool(doc.response_due_on and get_datetime(doc.response_due_on)<now_datetime() and doc.status not in CLOSED_STATUSES))

def _validate_classification(doc,settings):
    case_type=frappe.get_doc("Accountability Case Type",doc.case_type);category=frappe.get_doc("Accountability Category",doc.category);channel=frappe.get_doc("Accountability Channel",doc.channel)
    if not case_type.enabled or not category.enabled or not channel.enabled:frappe.throw(_("Case Type, Category, and Channel must be enabled."))
    if doc.anonymous and (not settings.allow_anonymous_cases or not case_type.allow_anonymous or not channel.allows_anonymous):frappe.throw(_("Anonymous submission is not allowed for the selected type or channel."))
    if channel.requires_contact and not doc.anonymous and not (doc.email or doc.mobile_no or doc.contact or doc.employee or doc.external_person or doc.supplier):frappe.throw(_("The selected channel requires contact details."))
    if doc.is_new():
        doc.confidentiality=category.default_confidentiality or case_type.default_confidentiality or doc.confidentiality
        doc.priority=category.default_priority or doc.priority
    if category.sensitive_category and doc.confidentiality=="Standard":doc.confidentiality=category.default_confidentiality or "Restricted"
    if category.requires_investigation or case_type.investigation_default:doc.investigation_required=1
    doc.receiving_role=doc.receiving_role or category.default_receiving_role or settings.default_accountability_role
    doc.receiving_department=doc.receiving_department or category.default_department

def _validate_reporter(doc,settings):
    if doc.anonymous:
        doc.stakeholder_type="Anonymous"
        for field in ("reporter_name","email","mobile_no","employee","external_person","supplier","contact"):doc.set(field,None)
        doc.consent_to_contact=0
    elif doc.stakeholder_type=="Anonymous":frappe.throw(_("Select Anonymous when Stakeholder Type is Anonymous."))
    elif not doc.reporter_name and not any((doc.employee,doc.external_person,doc.supplier,doc.contact)):frappe.throw(_("Reporter Name or a linked stakeholder record is required."))
    if doc.stakeholder_type=="Employee" and not doc.employee:frappe.throw(_("Employee is required for Employee stakeholder cases."))
    if doc.stakeholder_type in ("Supplier","Service Provider") and not doc.supplier:frappe.throw(_("Supplier is required for supplier or service provider cases."))
    if doc.consent_to_contact and not (doc.email or doc.mobile_no or doc.contact or doc.employee or doc.external_person or doc.supplier):frappe.throw(_("A contact method is required when consent is given."))

def _validate_context(doc):
    if doc.project and frappe.db.get_value("Project",doc.project,"company") not in (None,"",doc.company):frappe.throw(_("Project must belong to the selected Company."))
    if doc.related_name and not doc.related_doctype:frappe.throw(_("Related Document Type is required."))
    if doc.related_doctype and doc.related_name and not frappe.db.exists(doc.related_doctype,doc.related_name):frappe.throw(_("Related Document does not exist."))
    if doc.procurement_process:
        domain=frappe.db.get_value("Accountability Category",doc.category,"domain")
        if domain not in ("Procurement","Supplier Performance","Fraud and Corruption"):frappe.throw(_("Procurement Process requires a procurement, supplier, or fraud category."))
        if frappe.db.get_value("Procurement Process",doc.procurement_process,"company")!=doc.company:frappe.throw(_("Procurement Process must belong to the selected Company."))

def _validate_links(doc):
    if doc.custom_current_responsible_user and not frappe.db.exists("User",{"name":doc.custom_current_responsible_user,"enabled":1}):frappe.throw(_("Current Responsible User must be enabled."))
    if doc.receiving_role and doc.custom_current_responsible_user and not frappe.db.exists("Has Role",{"parent":doc.custom_current_responsible_user,"role":doc.receiving_role}):frappe.throw(_("Current Responsible User must have the Receiving Role."))

def _apply_initial_sla(doc,settings):
    ct=frappe.get_doc("Accountability Case Type",doc.case_type)
    if not doc.acknowledgement_due_on:doc.acknowledgement_due_on=add_days(doc.received_on,int(ct.acknowledgement_days if ct.acknowledgement_days is not None else settings.default_acknowledgement_days))
    if not doc.triage_due_on:
        days=ct.triage_days if ct.triage_days is not None else settings.default_triage_days
        doc.triage_due_on=add_days(doc.received_on,int(days))
    if not doc.response_due_on:
        complex_case=doc.priority in ({"High","Critical"} if settings.complex_priority_threshold=="High" else {"Critical"})
        days=settings.complex_response_days if complex_case else (ct.response_days if ct.response_days is not None else settings.default_response_days)
        doc.response_due_on=add_days(doc.received_on,int(days))
    update_days=ct.update_frequency_days if ct.update_frequency_days is not None else settings.update_frequency_days
    if not doc.next_reporter_update_due_on:
        doc.next_reporter_update_due_on=add_days(doc.last_update_to_reporter_on or doc.received_on,int(update_days))
    doc.reporter_update_overdue=int(bool(doc.next_reporter_update_due_on and get_datetime(doc.next_reporter_update_due_on)<now_datetime() and doc.status not in CLOSED_STATUSES))

def _protect_sensitive_changes(doc):
    old=doc.get_doc_before_save()
    if old and old.confidentiality in SENSITIVE_LEVELS and not _is_privileged_user(doc,frappe.session.user):
        protected=("confidentiality","category","case_type","receiving_role","receiving_department","custom_current_responsible_user")
        if any(doc.get(x)!=old.get(x) for x in protected):frappe.throw(_("Only an authorized manager may change sensitive classification or routing."),frappe.PermissionError)

def _validate_status(doc):
    old=doc.get_doc_before_save()
    if old and old.status=="Closed" and doc.status not in ("Closed","Reopened"):frappe.throw(_("A closed case must be reopened first."))
    if doc.status=="Closed":
        if not doc.resolution_decision or not doc.closure_rationale:frappe.throw(_("Resolution Decision and Closure Rationale are required."))
        if frappe.db.get_value("Accountability Case Type",doc.case_type,"requires_response") and not doc.response_logs:frappe.throw(_("At least one response is required."))
        doc.closed_on=doc.closed_on or now_datetime();doc.closed_by=doc.closed_by or frappe.session.user

def _is_privileged_user(doc,user):
    return user=="Administrator" or bool(set(frappe.get_roles(user)).intersection({"System Manager","Accountability Manager"})) or user in {doc.custom_current_responsible_user,doc.owner}
