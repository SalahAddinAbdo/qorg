from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import now_datetime

MANAGERS={"System Manager","Compliance Manager","Accountability Manager"}
def _manager():
    if frappe.session.user!="Administrator" and not MANAGERS.intersection(frappe.get_roles()): frappe.throw(_("Governance manager role is required."),frappe.PermissionError)
def _doc(dt,name):
    d=frappe.get_doc(dt,name)
    if not frappe.has_permission(dt,"write",doc=d): frappe.throw(_("Not permitted."),frappe.PermissionError)
    return d

@frappe.whitelist(methods=["POST"])
def add_risk_assessment(name,assessment_type,likelihood,impact,residual_likelihood,residual_impact,control_effectiveness=0,notes=None):
    d=_doc("Enterprise Risk",name); d.append("assessments",{"assessment_on":now_datetime(),"assessed_by":frappe.session.user,"assessment_type":assessment_type,"likelihood":likelihood,"impact":impact,"residual_likelihood":residual_likelihood,"residual_impact":residual_impact,"control_effectiveness":control_effectiveness,"notes":notes}); d.status="Monitoring" if d.status=="Treatment In Progress" else "Open"; d.save(); return d.name
@frappe.whitelist(methods=["POST"])
def activate_risk(name):
    d=_doc("Enterprise Risk",name)
    if d.status!="Draft" or not d.assessments: frappe.throw(_("A draft risk requires an assessment before activation."))
    d.status="Escalated" if d.escalation_required else "Open"; d.save(); return d.name
@frappe.whitelist(methods=["POST"])
def close_risk(name,closure_notes,closure_evidence):
    _manager(); d=_doc("Enterprise Risk",name); d.status="Closed"; d.closure_notes=closure_notes; d.closure_evidence=closure_evidence; d.save(); return d.name
@frappe.whitelist(methods=["POST"])
def add_compliance_review(name,review_type,status,review_notes,evidence=None,next_review_date=None):
    d=_doc("Compliance Obligation",name); d.append("reviews",{"reviewed_on":now_datetime(),"reviewed_by":frappe.session.user,"review_type":review_type,"status":status,"review_notes":review_notes,"evidence":evidence,"next_review_date":next_review_date}); d.status="Under Review"; d.save(); return d.name
@frappe.whitelist(methods=["POST"])
def verify_finding(name,effectiveness,verification_method,verification_evidence,closure_notes=None):
    _manager(); d=_doc("Assurance Finding",name)
    if d.status not in ("Pending Verification","In Progress","Action Agreed"): frappe.throw(_("Finding is not ready for verification."))
    d.effectiveness=effectiveness; d.verification_method=verification_method; d.verification_evidence=verification_evidence; d.verified_by=frappe.session.user; d.verified_on=now_datetime(); d.closure_notes=closure_notes; d.status="Closed" if effectiveness=="Effective" else "In Progress"; d.save(); return d.name
