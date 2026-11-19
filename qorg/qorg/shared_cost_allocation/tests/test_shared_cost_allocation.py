import unittest
from types import SimpleNamespace
from unittest.mock import patch
from qorg.qorg.shared_cost_allocation.validation import validate_rule,_validate_indirect
from qorg.qorg.shared_cost_allocation.engine import _next_version
class TestSharedCostAllocationValidation(unittest.TestCase):
 @patch("qorg.qorg.shared_cost_allocation.validation._validate_target")
 @patch("qorg.qorg.shared_cost_allocation.validation._validate_version")
 def test_fixed_percentages_must_equal_100(self,version,target):
  rows=[SimpleNamespace(idx=1,allow_allocation=1,project="P1",cost_center="C1",budget_line="B1",funding_agreement=None,allocation_percentage=60),SimpleNamespace(idx=2,allow_allocation=1,project="P2",cost_center="C2",budget_line="B2",funding_agreement=None,allocation_percentage=30)];doc=SimpleNamespace(effective_from="2026-01-01",effective_to=None,targets=rows,allocation_method="Fixed Percentage",allocation_category="Shared Operating Cost",source_selection_mode="Filtered GL Entries",selected_vouchers=[])
  with self.assertRaises(Exception):validate_rule(doc)
 def test_indirect_rate_periods_cannot_overlap(self):
  rows=[SimpleNamespace(effective_from="2026-01-01",effective_to="2026-06-30",indirect_cost_rate=7),SimpleNamespace(effective_from="2026-06-30",effective_to="2026-12-31",indirect_cost_rate=8)];doc=SimpleNamespace(indirect_cost_expense_account="E",indirect_cost_recovery_account="I",rate_periods=rows)
  with self.assertRaises(Exception):_validate_indirect(doc)
 def test_version_increment(self):self.assertEqual(_next_version("1.9"),"1.10")
