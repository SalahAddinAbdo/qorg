"""Pure-calculation tests (no database needed).

Run with:  bench --site <site> run-tests --module qorg.qorg.cost_distribution.tests.test_calculations
"""
import unittest
from types import SimpleNamespace as NS

import frappe

from qorg.qorg.cost_distribution.calculations import calculate_targets


def _profile(method, targets, difference="Allocate Rounding Difference", full=0):
    return NS(distribution_method=method, difference_handling=difference,
              require_full_distribution=full, targets=targets)


def _t(idx, pct=0, fixed=0, cap=0):
    return NS(idx=idx, allow_distribution=1, allocation_percentage=pct, fixed_amount=fixed,
              maximum_amount=cap, get=lambda k, _c=cap: _c if k == "maximum_amount" else None)


class TestCostDistributionCalculations(unittest.TestCase):
    def total(self, rows, key="allocated_amount"):
        return sum(r[key] for r in rows)

    def test_percentage_rounding_difference_goes_to_last_row(self):
        rows = calculate_targets(_profile("Fixed Percentage", [_t(1, 33.33), _t(2, 33.33), _t(3, 33.34)]), 100, 100, precision=2)
        self.assertAlmostEqual(self.total(rows), 100, places=2)

    def test_zero_decimal_currency(self):
        rows = calculate_targets(_profile("Equal Distribution", [_t(1), _t(2), _t(3)]), 100, 100, precision=0)
        self.assertEqual([r["allocated_amount"] for r in rows], [33, 33, 34])

    def test_three_decimal_currency(self):
        rows = calculate_targets(_profile("Equal Distribution", [_t(1), _t(2), _t(3)]), 10, 10, precision=3)
        self.assertAlmostEqual(self.total(rows), 10, places=3)

    def test_negative_amount_mirrors_positive(self):
        p = _profile("Fixed Percentage", [_t(1, 60), _t(2, 40)])
        pos = calculate_targets(p, 250.55, 250.55, precision=2)
        neg = calculate_targets(p, -250.55, -250.55, precision=2)
        self.assertEqual([-r["allocated_amount"] for r in neg], [r["allocated_amount"] for r in pos])

    def test_cap_is_checked_after_rounding_difference(self):
        p = _profile("Fixed Percentage", [_t(1, 33.33), _t(2, 33.33), _t(3, 33.33, cap=33.33)])
        with self.assertRaises(Exception):
            calculate_targets(p, 100, 100, precision=2)

    def test_reject_difference(self):
        p = _profile("Equal Distribution", [_t(1), _t(2), _t(3)], difference="Reject Difference")
        with self.assertRaises(Exception):
            calculate_targets(p, 100, 100, precision=2)

    def test_fixed_amount_exceeding_source_is_rejected(self):
        with self.assertRaises(Exception):
            calculate_targets(_profile("Fixed Amount", [_t(1, fixed=70), _t(2, fixed=40)]), 100, 100, precision=2)

    def test_fixed_amount_shortfall_is_not_hidden_as_rounding(self):
        p = _profile("Fixed Amount", [_t(1, fixed=30), _t(2, fixed=30)], full=1)
        with self.assertRaises(Exception):
            calculate_targets(p, 100, 100, precision=2)
