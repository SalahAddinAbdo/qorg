import hashlib, json
import frappe
from frappe import _
from .decimal_utils import require_exact_hundred

EVALUATION_DOCTYPES = {
    "Preliminary": "Procurement Preliminary Examination",
    "Technical": "Procurement Technical Evaluation",
    "Financial": "Procurement Financial Evaluation",
}

def snapshot_payload(doc):
    criteria = [r.as_dict(no_nulls=True) for r in doc.get("criteria") or []]
    payload = {
        "policy_rule": doc.policy_rule,
        "procurement_method": doc.procurement_method,
        "procurement_type": doc.procurement_type,
        "technical_weight": doc.technical_weight or 0,
        "financial_weight": doc.financial_weight or 0,
        "technical_threshold": doc.technical_threshold or 0,
        "two_envelope": int(doc.two_envelope or 0),
        "criteria": criteria,
    }
    return payload

def validate_process_setup(doc):
    components=[]
    if doc.technical_weight: components.append(doc.technical_weight)
    if doc.financial_weight: components.append(doc.financial_weight)
    if components: require_exact_hundred(components, "evaluation component weights")
    grouped={}
    for row in doc.get("criteria") or []:
        if row.get("weight") and row.get("component") not in ("Preliminary", None, ""):
            grouped.setdefault(row.component, []).append(row.weight)
    for component, weights in grouped.items():
        require_exact_hundred(weights, f"{component} criterion weights")

def freeze_setup(doc):
    validate_process_setup(doc)
    payload=snapshot_payload(doc)
    raw=json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    doc.setup_frozen=1
    doc.frozen_hash=hashlib.sha256(raw.encode()).hexdigest()
    doc.policy_snapshot=raw
    return doc.frozen_hash

def assert_not_frozen(doc):
    if not doc.is_new() and doc.setup_frozen:
        old=frappe.get_doc(doc.doctype,doc.name)
        protected=("policy_rule","procurement_method","procurement_type","technical_weight","financial_weight","technical_threshold","two_envelope")
        changed=[f for f in protected if doc.get(f)!=old.get(f)]
        if changed or doc.get("criteria") != old.get("criteria"):
            frappe.throw(_("Frozen procurement setup cannot be changed. Create a Procurement Amendment."))

def copy_template(process, template_name, component):
    if not template_name: return
    template=frappe.get_doc("Procurement Evaluation Template",template_name)
    process.set("criteria", [r for r in process.get("criteria") if r.component != component])
    for row in template.criteria:
        process.append("criteria", {"component":component,"criterion":row.criterion,"scoring_method":row.scoring_method,"maximum_score":row.maximum_score,"weight":row.weight,"mandatory":row.mandatory,"minimum_passing_score":row.minimum_passing_score,"description":row.description})

def generate_evaluation_documents(process_name):
    process=frappe.get_doc("Procurement Process",process_name)
    submissions=frappe.get_all("Procurement Submission",filters={"procurement_process":process.name,"docstatus":1},fields=["name","supplier"])
    method=frappe.get_doc("Procurement Method",process.procurement_method)
    created=[]
    for item in submissions:
        if not frappe.db.exists("Procurement Preliminary Examination",{"procurement_process":process.name,"submission":item.name}):
            d=frappe.get_doc({"doctype":"Procurement Preliminary Examination","procurement_process":process.name,"submission":item.name,"result":"Pending"}).insert(ignore_permissions=True); created.append(d.name)
        if method.requires_technical_evaluation and not frappe.db.exists("Procurement Technical Evaluation",{"procurement_process":process.name,"submission":item.name}):
            d=frappe.get_doc({"doctype":"Procurement Technical Evaluation","procurement_process":process.name,"submission":item.name,"supplier":item.supplier,"evaluation_mode":"Individual","technical_threshold":process.technical_threshold,"result":"Pending"}).insert(ignore_permissions=True); created.append(d.name)
    return created
