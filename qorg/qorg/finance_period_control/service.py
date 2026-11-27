import frappe
from frappe.utils import getdate, flt, today


def get_control_policy(company, project=None):
    from qorg.qorg.finance_period_control.policy_v2 import policy
    return policy(company, project)

ALLOWED_TRANSACTION_TYPES={"Commitment","Actual","Allocation","Transfer"}

def _period(name, company, posting_date, require_open):
    period=frappe.get_doc("Budget Period",name)
    if period.company!=company: frappe.throw(f"Budget Period {name} does not belong to {company}")
    if not (getdate(period.from_date)<=getdate(posting_date)<=getdate(period.to_date)):
        frappe.throw(f"Posting date is outside Budget Period {name}")
    if require_open and period.status!="Open": frappe.throw(f"Budget Period {name} is not Open")
    return period

def _rule_period(company, posting_date, project=None, reference_doctype=None, transaction_type=None):
    filters={"enabled":1,"company":company}
    rows=frappe.get_all("Budget Period Resolution Rule",filters=filters,fields=["name","project","reference_doctype","transaction_type","budget_period","valid_from","valid_to","priority"],order_by="priority asc, modified desc")
    matches=[]
    for r in rows:
        if r.project and r.project!=project: continue
        if r.reference_doctype and r.reference_doctype!=reference_doctype: continue
        if r.transaction_type and r.transaction_type!=transaction_type: continue
        if r.valid_from and getdate(posting_date)<getdate(r.valid_from): continue
        if r.valid_to and getdate(posting_date)>getdate(r.valid_to): continue
        specificity=sum(bool(x) for x in (r.project,r.reference_doctype,r.transaction_type,r.valid_from,r.valid_to))
        matches.append((r.priority,-specificity,r))
    if not matches: return None
    matches.sort(key=lambda x:(x[0],x[1],x[2].name))
    top=matches[0]
    tied=[x for x in matches if x[:2]==top[:2]]
    periods={x[2].budget_period for x in tied}
    if len(periods)>1: frappe.throw("Ambiguous Budget Period Resolution Rules at the same priority and specificity")
    return top[2]

def resolve_budget_period(company, posting_date, project=None, explicit=None, require_open=True, reference_doctype=None, transaction_type=None):
    if not company: frappe.throw("Company is required to resolve the Budget Period")
    if get_control_policy(company, project)=="Disabled": frappe.throw("Period Budget Control is disabled for this Project or Company")
    posting_date=getdate(posting_date or today())
    if transaction_type and transaction_type not in ALLOWED_TRANSACTION_TYPES: frappe.throw("Unsupported transaction type")
    if explicit: return _period(explicit,company,posting_date,require_open),"Explicit"
    rule=_rule_period(company,posting_date,project,reference_doctype,transaction_type)
    if rule: return _period(rule.budget_period,company,posting_date,require_open),f"Rule:{rule.name}"
    project_period=project and frappe.db.get_value("Project",project,"qorg_default_budget_period")
    if project_period: return _period(project_period,company,posting_date,require_open),"Project"
    company_period=frappe.db.get_value("Company",company,"qorg_default_budget_period")
    if company_period: return _period(company_period,company,posting_date,require_open),"Company"
    rows=frappe.get_all("Budget Period",filters={"company":company,"from_date":["<=",posting_date],"to_date":[">=",posting_date]},fields=["name"],order_by="is_default desc, from_date desc")
    if not rows: frappe.throw(f"No Budget Period covers {posting_date} for {company}")
    if len(rows)>1: frappe.throw(f"More than one Budget Period covers {posting_date} for {company}")
    return _period(rows[0].name,company,posting_date,require_open),"Posting Date"

def validate_budget_line(doc, method=None):
    total=0;seen=set()
    for row in doc.get("period_allocations") or []:
        if row.budget_period in seen: frappe.throw(f"Duplicate Budget Period allocation: {row.budget_period}")
        seen.add(row.budget_period);total+=flt(row.allocated_amount)
        period=frappe.get_cached_doc("Budget Period",row.budget_period)
        project_company=doc.project and frappe.db.get_value("Project",doc.project,"company")
        if project_company and period.company!=project_company: frappe.throw("Allocation period must belong to the Project Company")
    doc.allocation_total=total

def validate_commitment_ledger(doc, method=None):
    from qorg.qorg.finance_period_control.commitment_lifecycle import validate_lifecycle
    validate_lifecycle(doc)
    if doc.project:
        project_company=frappe.db.get_value("Project",doc.project,"company")
        if project_company and project_company!=doc.company: frappe.throw("Project must belong to the selected Company")
    if doc.budget_line:
        line_project=frappe.db.get_value("Budget Line",doc.budget_line,"project")
        if line_project and doc.project and line_project!=doc.project: frappe.throw("Budget Line must belong to the selected Project")
    if not doc.company:return
    if get_control_policy(doc.company, doc.project)=="Disabled":
        doc.budget_period=None;doc.budget_period_source="Disabled";return
    dates=[r.posting_date for r in (doc.get("entries") or []) if r.posting_date]
    posting_date=max(dates or [today()])
    period,source=resolve_budget_period(doc.company,posting_date,doc.project,doc.budget_period or None,True,"Commitment Ledger","Commitment")
    doc.budget_period=period.name;doc.budget_period_source=source

@frappe.whitelist()
def preview_resolution(company, posting_date, project=None, reference_doctype=None, transaction_type=None, explicit=None):
    frappe.has_permission("Budget Period", "read", throw=True)
    period,source=resolve_budget_period(company,posting_date,project,explicit,False,reference_doctype,transaction_type)
    return {"budget_period":period.name,"period_name":period.period_name,"from_date":period.from_date,"to_date":period.to_date,"status":period.status,"source":source}
