"""Pure Decimal-based allocation primitives. No Frappe imports."""
from __future__ import annotations
from decimal import Decimal, ROUND_HALF_UP

D = Decimal

def decimal(value):
    return D(str(value or 0))

def quantize(value, precision=2):
    return decimal(value).quantize(D(1).scaleb(-int(precision)), rounding=ROUND_HALF_UP)

def normalize_shares(rows):
    total = sum((decimal(row["share"]) for row in rows), D("0"))
    if total <= 0:
        raise ValueError("Allocation shares must be greater than zero")
    return [{**row, "share": decimal(row["share"]) * D("100") / total} for row in rows]

def split_amount(amount, rows, precision=2):
    rows = normalize_shares(rows)
    source = quantize(amount, precision)
    output = []
    assigned = D("0")
    for index, row in enumerate(rows):
        value = source - assigned if index == len(rows) - 1 else quantize(source * row["share"] / D("100"), precision)
        assigned += value
        output.append({**row, "amount": value})
    return output

def shares_from_amounts(amounts):
    total = sum((decimal(value) for value in amounts.values()), D("0"))
    if total <= 0:
        raise ValueError("Allocation basis total must be greater than zero")
    return {key: decimal(value) * D("100") / total for key, value in amounts.items()}

def eligible_split(amount, percentage=100, maximum=None, precision=2):
    amount = quantize(amount, precision)
    eligible = quantize(amount * decimal(percentage) / D("100"), precision)
    if maximum not in (None, ""):
        eligible = min(eligible, quantize(maximum, precision))
    return eligible, quantize(amount - eligible, precision)

def assert_fully_allocated(source, allocations, precision=2):
    source = quantize(source, precision)
    assigned = quantize(sum((decimal(value) for value in allocations), D("0")), precision)
    if source != assigned:
        raise ValueError(f"Allocation difference is {source - assigned}")
    return True
