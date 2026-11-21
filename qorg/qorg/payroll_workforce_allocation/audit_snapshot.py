import json
from .utils import stable_hash

def build_snapshot(run):
    data={"engine_version":"3.0.2","payroll_entry":run.payroll_entry,"source_fingerprint":run.source_fingerprint,"results":[{"salary_slip":r.salary_slip,"salary_component":r.salary_component,"project":r.project,"funding_agreement":r.funding_agreement,"budget_line":r.budget_line,"amount":r.allocated_amount,"policy":r.policy_reference,"dimensions":r.dimension_snapshot} for r in run.result_rows],"exceptions":[{"type":r.exception_type,"severity":r.severity,"resolved":r.resolved,"reference":r.approval_reference} for r in run.exceptions]}
    return json.dumps(data,sort_keys=True,default=str), stable_hash(data)
