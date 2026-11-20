"""Deterministic target calculation for Cost Distribution Profiles.

Rules enforced here (server side):

* Amounts are rounded with Frappe's ``flt`` using the system currency precision,
  never with Python's built-in ``round`` and never with a hard-coded two decimals.
* Negative source amounts (returns / credit notes) are distributed on their
  absolute value and the sign is re-applied, so the same profile or snapshot
  produces a mirror-image distribution.
* The Maximum Amount cap is checked on the *final* value of every target,
  including the value that receives the rounding difference.
* ``difference_handling`` is honoured: Allocate Rounding Difference,
  Leave Unallocated and Reject Difference.
"""
from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint, flt

SUPPORTED_METHODS = ("Fixed Percentage", "Fixed Amount", "Equal Distribution")


def _precision(precision=None) -> int:
    if precision is not None:
        return cint(precision)
    return cint(frappe.get_system_settings("currency_precision")) or 2


def calculate_targets(profile, amount, base_amount=None, precision=None):
    targets = [x for x in profile.targets if x.allow_distribution]
    if not targets:
        return []
    if profile.distribution_method not in SUPPORTED_METHODS:
        frappe.throw(_("Distribution Method {0} is not implemented.").format(profile.distribution_method))

    precision = _precision(precision)
    amount = flt(amount, precision)
    base_amount = flt(base_amount if base_amount is not None else amount, precision)
    sign = -1 if amount < 0 else 1
    amount, base_amount = abs(amount), abs(base_amount)
    tolerance = flt(10 ** -precision, precision + 2)

    if profile.distribution_method == "Fixed Amount":
        fixed_total = sum(flt(x.fixed_amount, precision) for x in targets)
        if fixed_total - amount > tolerance:
            frappe.throw(_("Fixed target amounts exceed the source amount."))

    remaining, base_remaining = amount, base_amount
    last = len(targets) - 1
    rows = []
    for idx, target in enumerate(targets):
        if profile.distribution_method == "Fixed Percentage":
            ratio = flt(target.allocation_percentage) / 100
            value, base = amount * ratio, base_amount * ratio
        elif profile.distribution_method == "Fixed Amount":
            value = flt(target.fixed_amount, precision)
            base = value * (base_amount / amount if amount else 1)
        else:
            value, base = amount / len(targets), base_amount / len(targets)

        value, base = flt(value, precision), flt(base, precision)

        if idx == last and profile.difference_handling == "Allocate Rounding Difference":
            # Absorb only genuine rounding residue; a Fixed Amount shortfall is
            # not a rounding difference and must stay visible.
            residue = flt(remaining - value, precision)
            if profile.distribution_method != "Fixed Amount" or abs(residue) <= tolerance * len(targets):
                value = flt(remaining, precision)
                base = flt(base_remaining, precision)

        cap = flt(target.maximum_amount, precision) if target.get("maximum_amount") else 0
        if cap and value - cap > tolerance:
            frappe.throw(_("Target row {0} exceeds Maximum Amount.").format(target.idx))

        remaining = flt(remaining - value, precision)
        base_remaining = flt(base_remaining - base, precision)
        rows.append({"target": target, "allocated_amount": value * sign, "base_amount": base * sign})

    difference = flt(remaining, precision)
    if profile.difference_handling == "Reject Difference" and abs(difference) > 0:
        frappe.throw(_("The distribution leaves an unallocated difference of {0}; the profile rejects differences.").format(difference))
    if profile.require_full_distribution and abs(difference) > tolerance:
        frappe.throw(_("Full distribution is required."))
    return rows
