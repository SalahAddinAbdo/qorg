import frappe
from frappe import _
from frappe.utils import getdate
from .utils import stable_hash
def component_fingerprint(name):
    fields=["type","salary_component_abbr","condition","amount_based_on_formula","formula","depends_on_payment_days","is_tax_applicable","is_statistical_component","do_not_include_in_total","variable_based_on_taxable_salary"]
    meta=frappe.get_meta("Salary Component"); fields=[x for x in fields if meta.has_field(x)]
    return stable_hash(frappe.db.get_value("Salary Component",name,fields,as_dict=True) or {})
def validate_policy(doc):
    if doc.effective_to and getdate(doc.effective_to)<getdate(doc.effective_from): frappe.throw(_("Effective To cannot precede Effective From."))
    seen=set()
    for rule in doc.component_rules or []:
        if rule.salary_component in seen: frappe.throw(_("Duplicate Salary Component: {0}").format(rule.salary_component))
        seen.add(rule.salary_component)
        if rule.funding_treatment=="Requires Approval": rule.requires_prior_approval=1
        if rule.funding_treatment=="Eligible": rule.eligible_percentage=100
        if rule.funding_treatment=="Ineligible": rule.eligible_percentage=0
        rule.component_fingerprint=component_fingerprint(rule.salary_component)
        if rule.funding_treatment=="Partially Eligible" and not (0<=float(rule.eligible_percentage or 0)<100): frappe.throw(_("Partially eligible rules require a percentage below 100."))
        if rule.allocation_basis in ("Basic Salary Allocation", "Source Component Allocation") and not rule.source_salary_component: frappe.throw(_("Source Salary Component is required."))
    doc.fingerprint=stable_hash([r.as_dict() for r in doc.component_rules or []])
def activate_policy(doc):
    doc.db_set("status","Active",update_modified=False)
    if doc.supersedes_policy: frappe.db.set_value("Payroll Cost Policy",doc.supersedes_policy,"status","Superseded",update_modified=False)
def cancel_policy(doc): doc.db_set("status","Expired",update_modified=False)
def effective_policy(company,on_date,funding_agreement=None,donor=None):
    base={"company":company,"docstatus":1,"effective_from":["<=",on_date]}
    candidates=frappe.get_all("Payroll Cost Policy",filters=base,fields=["name","funding_agreement","donor","priority","effective_to"],order_by="priority desc",limit_page_length=0)
    valid=[]
    for row in candidates:
        if row.effective_to and getdate(row.effective_to)<getdate(on_date): continue
        score=0
        if row.funding_agreement:
            if row.funding_agreement!=funding_agreement: continue
            score=300
        elif row.donor:
            if row.donor!=donor: continue
            score=200
        else: score=100
        valid.append((score+int(row.priority or 0),row.name))
    return frappe.get_doc("Payroll Cost Policy",max(valid)[1]) if valid else None
