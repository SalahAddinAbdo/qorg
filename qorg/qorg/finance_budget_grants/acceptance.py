from __future__ import annotations
from .audit import audit_runtime_configuration
from .reconciliation import audit_financial_integrity
from .closeout import closeout_gate

def run_acceptance(project=None):
    runtime=audit_runtime_configuration()
    integrity=audit_financial_integrity(project)
    closeout=closeout_gate(project) if project else None
    passed=bool(runtime.get("passed_core_dimension_check") and integrity.get("passed") and (not closeout or closeout.get("status") != "Blocked"))
    return {"runtime":runtime,"integrity":integrity,"closeout":closeout,"passed":passed}
