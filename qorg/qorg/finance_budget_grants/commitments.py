from __future__ import annotations
from collections import defaultdict
import frappe
from frappe.utils import flt

UPSTREAM_STAGES = ("Requested", "Reserved", "Ordered", "Contracted", "Received", "Accepted")
ALL_STAGES = UPSTREAM_STAGES + ("Invoiced", "Paid", "Released", "Cancelled")

def _signed(row):
    return flt(row.amount) * (-1 if row.direction == "Decrease" else 1)

def commitment_snapshot(project=None, budget_line=None, company=None, currency=None):
    filters = {"docstatus": 1}
    for key, value in (("project", project), ("budget_line", budget_line), ("company", company), ("currency", currency)):
        if value:
            filters[key] = value
    totals = defaultdict(float)
    chains = []
    for name in frappe.get_all("Commitment Ledger", filters=filters, pluck="name"):
        ledger = frappe.get_doc("Commitment Ledger", name)
        stages = defaultdict(float)
        references = []
        for row in ledger.get("entries") or []:
            stages[row.stage] += _signed(row)
            references.append((row.reference_doctype, row.reference_name, row.stage))
        upstream = max([max(stages.get(stage, 0), 0) for stage in UPSTREAM_STAGES] or [0])
        invoiced = max(stages.get("Invoiced", 0), 0)
        released = max(-(stages.get("Released", 0) + stages.get("Cancelled", 0)), 0)
        open_amount = max(upstream - invoiced - released, 0)
        for stage in ALL_STAGES:
            totals[stage.lower()] += stages.get(stage, 0)
        totals["open_commitment"] += open_amount
        chains.append({
            "ledger": ledger.name,
            "company": ledger.company,
            "project": ledger.project,
            "budget_line": ledger.budget_line,
            "currency": ledger.currency,
            "open_commitment": flt(open_amount),
            "stages": dict(stages),
            "references": references,
        })
    result = {key: flt(value) for key, value in totals.items()}
    result["chains"] = chains
    return result

def get_open_commitments(project=None, budget_line=None, company=None, currency=None):
    snapshot = commitment_snapshot(project, budget_line, company, currency)
    snapshot["initial_commitment"] = flt(snapshot.get("requested")) + flt(snapshot.get("reserved"))
    snapshot["contract_commitment"] = flt(snapshot.get("contracted"))
    return snapshot
