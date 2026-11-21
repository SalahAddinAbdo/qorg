import frappe
from frappe import _
from frappe.utils import flt
from .funding_plan import get_effective_plan
from .component_policy import effective_policy, component_fingerprint
from .effort import resolve_effort
from .eligibility import donor_for_agreement, eligible_amount, validate_destination
from .dimensions import resolve_dimensions, validate_dimensions, snapshot
from .origin import explicit_origin
from .allocation_basis import resolve_basis
from .calculation import split_amount
from .utils import stable_hash, payroll_source_fingerprint
from .currency import company_currency, convert

COST_TREATMENTS = {"Allocable Earning", "Employer Contribution"}

def _exception_key(values): return stable_hash({k:values.get(k) for k in ("employee","salary_slip","salary_component","exception_type","source_fingerprint")})
def _exception(run, **values):
    values.setdefault("source_fingerprint",run.source_fingerprint);values.setdefault("exception_key",_exception_key(values));run.append("exceptions",values)
def _salary_rows(slip):
    return [(table, row) for table in ("earnings", "deductions") for row in (slip.get(table) or [])]
def _rule(policy, component):
    return next((row for row in (policy.component_rules if policy else []) if row.salary_component == component), None)
def _policy_and_rule(run, destination, component):
    donor = donor_for_agreement(destination.get("funding_agreement"))
    policy = effective_policy(run.company, run.end_date, destination.get("funding_agreement"), donor)
    return policy, _rule(policy, component)
def _component_rule(run, effort, component):
    resolved=[]
    for destination in effort:
        policy, rule = _policy_and_rule(run, destination, component)
        if not rule: return None, None
        resolved.append((policy, rule))
    signatures={(row.cost_treatment,row.allocation_basis,row.source_salary_component,row.funding_treatment,flt(row.eligible_percentage),flt(row.maximum_eligible_amount),row.requires_prior_approval) for _,row in resolved}
    if len(signatures)>1: return "CONFLICT", None
    return resolved[0]
def _taxable(detail):
    return bool(detail.get("is_tax_applicable") or detail.get("variable_based_on_taxable_salary")) and not detail.get("exempted_from_income_tax")
def _precision(slip):
    return frappe.get_precision("Salary Slip", "net_pay", slip) or 2
def _basis_rows(run, slip, detail, rule, effort, distributions, taxable, net):
    explicit = explicit_origin(detail, effort) if rule.allocation_basis == "Explicit Origin" else None
    rows = resolve_basis(rule, effort, distributions, taxable, net, explicit)
    if not rows:
        _exception(run, employee=slip.employee, salary_slip=slip.name, salary_component=detail.salary_component, exception_type="Allocation Gap", severity="Blocker", description=_("No allocation evidence was resolved for basis {0}.").format(rule.allocation_basis), amount=detail.amount)
    return rows

def _append_result(run, slip, detail, rule, destination, amount, ineligible, policy, source):
    dimensions=resolve_dimensions(destination,run.company,employee=slip.employee)
    for message in validate_dimensions(dimensions,run.company):
        _exception(run,employee=slip.employee,salary_slip=slip.name,salary_component=detail.salary_component,exception_type="Missing Dimension",severity="Blocker",description=message,amount=float(amount))
    run.append("result_rows",{"employee":slip.employee,"salary_slip":slip.name,"salary_component":detail.salary_component,"component_category":rule.cost_treatment,"component_amount":detail.amount,"allocation_basis":rule.allocation_basis,"work_share":float(destination.share),"eligible_percentage":rule.eligible_percentage or 100,"allocated_amount":float(amount),"ineligible_amount":float(ineligible),"currency":slip.currency or company_currency(run.company),"exchange_rate":convert(1, slip.currency or company_currency(run.company), company_currency(run.company), run.posting_date or run.end_date)[1],"company_currency_amount":convert(amount, slip.currency or company_currency(run.company), company_currency(run.company), run.posting_date or run.end_date)[0],"project":destination.get("project"),"cost_center":destination.get("cost_center"),"funding_agreement":destination.get("funding_agreement"),"budget_line":destination.get("budget_line"),"funding_type":destination.get("funding_type"),"evidence_type":destination.get("evidence_type"),"evidence_reference":destination.get("evidence_reference"),"policy_reference":policy.name,"approval_reference_type":next((x.approval_reference_type for x in run.exceptions if x.salary_slip==slip.name and x.salary_component==detail.salary_component and x.resolved and x.approval_reference),None),"approval_reference":next((x.approval_reference for x in run.exceptions if x.salary_slip==slip.name and x.salary_component==detail.salary_component and x.resolved and x.approval_reference),None),"evidence_payload":destination.get("evidence_payload"),"dimension_snapshot":snapshot(dimensions),"source_fingerprint":stable_hash(source)})

def _allocate_component(run,slip,detail,policy,rule,basis_rows,source,total):
    precision=_precision(slip); allocated_map=[]
    for split in split_amount(detail.amount,[dict(row,share=row.share) for row in basis_rows],precision):
        destination=frappe._dict(split); gross=float(split["amount"])
        errors=validate_destination(destination,run.end_date,run.company,gross)
        for message in errors: _exception(run,employee=slip.employee,salary_slip=slip.name,salary_component=detail.salary_component,exception_type="Budget Unavailable" if "Budget" in message else "Expired Funding",severity="Blocker",description=message,amount=gross)
        funded=eligible_amount(gross,rule,precision); unfunded=flt(gross-funded,precision)
        if funded:
            _append_result(run,slip,detail,rule,destination,funded,0,policy,source);allocated_map.append((funded,destination))
            if rule.cost_treatment in COST_TREATMENTS: total["allocated"]+=funded
        if unfunded:
            if not rule.fallback_project:
                _exception(run,employee=slip.employee,salary_slip=slip.name,salary_component=detail.salary_component,exception_type="Ineligible Cost",severity="Blocker",description=_("Ineligible payroll cost has no approved fallback destination."),amount=unfunded);continue
            fallback=frappe._dict(project=rule.fallback_project,cost_center=None,funding_agreement=rule.fallback_funding_agreement,budget_line=rule.fallback_budget_line,funding_type="Organization Funded",share=destination.share,evidence_type="Policy Fallback",evidence_reference=policy.name)
            _append_result(run,slip,detail,rule,fallback,unfunded,unfunded,policy,source);allocated_map.append((unfunded,fallback))
            if rule.cost_treatment in COST_TREATMENTS: total["allocated"]+=unfunded
    return [dict(row,share=float(amount)) for amount,row in allocated_map]

def calculate_document(run):
    current_fingerprint=payroll_source_fingerprint(frappe,run.payroll_entry)
    approved={x.exception_key:x.as_dict() for x in (run.exceptions or []) if x.exception_type=="Missing Approval" and x.resolved and x.approval_reference and x.source_fingerprint==current_fingerprint}
    run.set("result_rows",[]);run.set("exceptions",[]);run.source_fingerprint=current_fingerprint
    payroll=frappe.get_doc("Payroll Entry",run.payroll_entry);run.company=payroll.company;run.start_date=payroll.start_date;run.end_date=payroll.end_date
    slips=frappe.get_all("Salary Slip",filters={"payroll_entry":payroll.name,"docstatus":1},pluck="name")
    if not slips: frappe.throw(_("No submitted Salary Slips were found for this Payroll Entry."))
    total={"gross":0,"deductions":0,"net":0,"employer":0,"employment":0,"allocated":0}
    for name in slips:
        slip=frappe.get_doc("Salary Slip",name);source=(name,slip.modified,slip.gross_pay,slip.total_deduction,slip.net_pay)
        total["gross"]+=flt(slip.gross_pay);total["deductions"]+=flt(slip.total_deduction);total["net"]+=flt(slip.net_pay)
        plan=get_effective_plan(slip.employee,run.end_date)
        if not plan: _exception(run,employee=slip.employee,salary_slip=slip.name,exception_type="Missing Plan",severity="Blocker",description=_("No active Workforce Funding Plan."));continue
        effort=resolve_effort(plan,slip.employee,run.start_date,run.end_date,run.payroll_entry)
        if not effort or abs(sum(flt(row.share) for row in effort)-100)>0.01: _exception(run,employee=slip.employee,salary_slip=slip.name,exception_type="Allocation Gap",severity="Blocker",description=_("Resolved work allocation does not total 100%."));continue
        rows=_salary_rows(slip);distributions={};taxable=[];net=[]
        ordered=sorted(rows,key=lambda item:{"Work Allocation":0,"Explicit Origin":0,"Basic Salary Allocation":1,"Source Component Allocation":1,"Taxable Earnings Allocation":2,"Net Pay Allocation":3,"Do Not Allocate":4}.get((_component_rule(run,effort,item[1].salary_component)[1] or frappe._dict(allocation_basis="Do Not Allocate")).allocation_basis,4))
        for table,detail in ordered:
            policy,rule=_component_rule(run,effort,detail.salary_component)
            if policy=="CONFLICT": _exception(run,employee=slip.employee,salary_slip=slip.name,salary_component=detail.salary_component,exception_type="Other",severity="Blocker",description=_("Component policy differs between funding destinations."));continue
            if not rule: _exception(run,employee=slip.employee,salary_slip=slip.name,salary_component=detail.salary_component,exception_type="Missing Plan",severity="Blocker",description=_("No effective Payroll Component Rule."),amount=detail.amount);continue
            if rule.component_fingerprint!=component_fingerprint(detail.salary_component): _exception(run,employee=slip.employee,salary_slip=slip.name,salary_component=detail.salary_component,exception_type="Component Changed",severity="Blocker",description=_("Salary Component changed after policy approval."));continue
            if rule.cost_treatment in ("Informational","Excluded") or rule.allocation_basis=="Do Not Allocate": continue
            if rule.requires_prior_approval:
                values={"employee":slip.employee,"salary_slip":slip.name,"salary_component":detail.salary_component,"exception_type":"Missing Approval","severity":"Blocker","description":_("Prior approval reference is required."),"amount":detail.amount,"required_action":_("Record an approval reference or attach approval evidence, then resolve the exception."),"source_fingerprint":run.source_fingerprint}
                key=_exception_key(values); prior=approved.get(key)
                if prior:
                    values.update({"severity":"Info","resolved":1,"resolution":prior.get("resolution"),"approval_reference_type":prior.get("approval_reference_type"),"approval_reference":prior.get("approval_reference"),"approval_attachment":prior.get("approval_attachment"),"approved_percentage":prior.get("approved_percentage"),"approved_amount":prior.get("approved_amount"),"approval_currency":prior.get("approval_currency"),"approved_by":prior.get("approved_by"),"approved_on":prior.get("approved_on"),"resolved_by":prior.get("resolved_by"),"resolved_on":prior.get("resolved_on")})
                    _exception(run,**values)
                else:
                    _exception(run,**values);continue
            if rule.cost_treatment in COST_TREATMENTS:
                total["employment"]+=flt(detail.amount)
                if rule.cost_treatment=="Employer Contribution":total["employer"]+=flt(detail.amount)
            basis=_basis_rows(run,slip,detail,rule,effort,distributions,taxable,net)
            if not basis: continue
            allocated=_allocate_component(run,slip,detail,policy,rule,basis,source,total)
            distributions[detail.salary_component]=allocated
            if table=="earnings" and _taxable(detail): taxable.append((detail.amount,allocated))
            if table=="earnings": net.append((detail.amount,allocated))
            elif rule.cost_treatment=="Employee Deduction": net.append((-flt(detail.amount),allocated))
    run.total_gross_earnings=total["gross"];run.total_employee_deductions=total["deductions"];run.total_net_pay=total["net"];run.total_employer_costs=total["employer"];run.total_employment_cost=total["employment"];run.total_allocated_cost=total["allocated"];run.allocation_difference=flt(total["employment"]-total["allocated"]);run.source_fingerprint=payroll_source_fingerprint(frappe,run.payroll_entry);run.status="Exceptions Found" if any(row.severity=="Blocker" and not row.resolved for row in run.exceptions) else "Ready for Approval";return run
