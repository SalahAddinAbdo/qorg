"""Resolve payroll component allocation bases without recalculating salary formulas."""
from decimal import Decimal
from .calculation import decimal, normalize_shares


def key_for(row):
    return (row.get("project"), row.get("cost_center"), row.get("funding_agreement"), row.get("budget_line"))


def aggregate_weighted(distributions):
    totals = {}
    template = {}
    for amount, rows in distributions:
        for row in rows:
            key = key_for(row)
            template[key] = row
            totals[key] = totals.get(key, Decimal("0")) + decimal(amount) * decimal(row["share"]) / Decimal("100")
    if not totals or sum(totals.values(), Decimal("0")) <= 0:
        return []
    result = [{**dict(template[key]), "share": value} for key, value in totals.items()]
    return normalize_shares(result)


def resolve_basis(rule, work_rows, source_distributions, taxable_distributions, net_distributions, explicit_rows=None):
    basis = rule.allocation_basis
    if basis == "Work Allocation":
        return work_rows
    if basis == "Explicit Origin":
        return explicit_rows or []
    if basis in ("Basic Salary Allocation", "Source Component Allocation"):
        return source_distributions.get(rule.source_salary_component) or []
    if basis == "Taxable Earnings Allocation":
        return aggregate_weighted(taxable_distributions)
    if basis == "Net Pay Allocation":
        return aggregate_weighted(net_distributions)
    if basis == "Do Not Allocate":
        return []
    return work_rows
