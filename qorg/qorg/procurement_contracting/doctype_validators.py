import re
import frappe
from frappe import _
from frappe.utils import flt, getdate
from .decimal_utils import require_exact_hundred
from .committee_engine import CommitteeMandate, CommitteeMember, validate_mandate
from .policy_engine import PolicyRule, validate_no_ambiguous_overlap


def validate_method(doc):
    weights=[flt(doc.default_technical_weight),flt(doc.default_financial_weight)]
    if any(weights): require_exact_hundred(weights,"default technical and financial weights")
    if doc.requires_two_envelope and not (doc.requires_technical_evaluation and doc.requires_financial_evaluation):
        frappe.throw(_("Two-envelope submission requires both technical and financial evaluation."))
    if doc.allows_direct_purchase_order and doc.requires_competition:
        frappe.throw(_("A method cannot allow direct Purchase Order and require competition simultaneously."))


def validate_policy_rule(doc):
    if flt(doc.maximum_amount) and flt(doc.maximum_amount)<flt(doc.minimum_amount):
        frappe.throw(_("Maximum amount cannot be lower than minimum amount."))
    if doc.effective_from and doc.effective_to and getdate(doc.effective_to)<getdate(doc.effective_from):
        frappe.throw(_("Effective To cannot precede Effective From."))
    current=PolicyRule(doc.name or "Current",doc.company,doc.currency,doc.procurement_type,doc.minimum_amount,doc.maximum_amount,doc.procurement_method,doc.priority or 0,doc.effective_from,doc.effective_to,doc.risk_level,doc.project,None,None,doc.emergency_only,doc.disabled,{})
    rows=[]
    for r in frappe.get_all("Procurement Policy Rule",filters={"name":["!=",doc.name or ""],"disabled":0},fields=["name","company","currency","procurement_type","minimum_amount","maximum_amount","procurement_method","priority","effective_from","effective_to","risk_level","project","emergency_only","disabled"]):
        rows.append(PolicyRule(r.name,r.company,r.currency,r.procurement_type,r.minimum_amount,r.maximum_amount,r.procurement_method,r.priority or 0,r.effective_from,r.effective_to,r.risk_level,r.project,None,None,r.emergency_only,r.disabled,{}))
    try: validate_no_ambiguous_overlap(rows+[current])
    except Exception as exc: frappe.throw(str(exc))


def validate_committee(doc):
    if getdate(doc.valid_to)<getdate(doc.valid_from): frappe.throw(_("Committee Valid To cannot precede Valid From."))
    members=tuple(CommitteeMember(r.user,r.committee_role,bool(r.voting_member),r.alternate_for,r.member_weight,bool(r.recused),bool(r.active)) for r in doc.members)
    try: validate_mandate(CommitteeMandate(doc.name or "Current",doc.committee_type,doc.company,getdate(doc.valid_from),getdate(doc.valid_to),doc.quorum,members,disabled=bool(doc.disabled)))
    except Exception as exc: frappe.throw(str(exc))
    chairs=[r for r in doc.members if r.active and r.committee_role=="Chair"]
    if len(chairs)!=1: frappe.throw(_("Exactly one active committee Chair is required."))


def validate_evaluation_template(doc):
    weighted=[r.weight for r in doc.criteria if r.weight]
    if weighted: require_exact_hundred(weighted,f"{doc.evaluation_component} template weights")
    names=[(r.criterion or "").strip().lower() for r in doc.criteria]
    if len(names)!=len(set(names)): frappe.throw(_("Evaluation criteria cannot be duplicated."))


def validate_notice(doc):
    if doc.deadline and doc.publish_on and doc.deadline<=doc.publish_on: frappe.throw(_("Submission deadline must be after publication date."))
    if doc.published and not doc.route: doc.route=re.sub(r"[^a-z0-9]+","-",(doc.title or doc.name).lower()).strip("-")


def validate_bid_opening(doc):
    if not doc.committee: frappe.throw(_("Bid Opening Committee is required."))
    if not doc.minutes: frappe.throw(_("Bid Opening Minutes are required."))


def validate_preliminary(doc):
    if doc.result in ("Non-Responsive","Disqualified") and not doc.reasons: frappe.throw(_("Reasons are required for exclusion or disqualification."))


def validate_award_recommendation(doc):
    summary=frappe.get_doc("Evaluation Summary",doc.evaluation_summary)
    if doc.recommended_supplier and summary.recommended_supplier and doc.recommended_supplier!=summary.recommended_supplier:
        frappe.throw(_("Recommended Supplier must match the approved evaluation summary."))


def validate_award_decision(doc):
    if doc.decision=="Approved" and not doc.awarded_supplier: frappe.throw(_("Awarded Supplier is required for an approved award decision."))


def validate_amendment(doc):
    if doc.extend_deadline and not doc.new_deadline: frappe.throw(_("New Deadline is required when extending the deadline."))
    if not doc.reason: frappe.throw(_("Amendment reason is required."))


def validate_clarification(doc):
    if doc.response and not doc.responded_on: doc.responded_on=frappe.utils.now_datetime()


def validate_complaint(doc):
    if doc.status=="Closed" and not (doc.decision and doc.closed_on): frappe.throw(_("Decision and Closed On are required before closing a complaint."))


def validate_framework(doc):
    if getdate(doc.valid_to)<getdate(doc.valid_from): frappe.throw(_("Framework validity end cannot precede its start."))
    if flt(doc.consumed_amount)>flt(doc.total_ceiling): frappe.throw(_("Consumed amount cannot exceed the total ceiling."))
    if doc.selection_method=="Direct Allocation" and len([r for r in doc.suppliers if r.active])!=1: frappe.throw(_("Direct Allocation requires exactly one active supplier."))
