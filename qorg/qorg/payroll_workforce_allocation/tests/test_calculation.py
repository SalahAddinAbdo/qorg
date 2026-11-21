import unittest
from decimal import Decimal
from qorg.qorg.payroll_workforce_allocation.calculation import split_amount, eligible_split, shares_from_amounts, assert_fully_allocated

class TestCalculation(unittest.TestCase):
    def test_rounding_is_absorbed_by_last_row(self):
        result = split_amount("100", [{"key":"A","share":33.33},{"key":"B","share":33.33},{"key":"C","share":33.34}], 2)
        self.assertEqual(sum(row["amount"] for row in result), Decimal("100.00"))
    def test_partial_eligibility(self):
        self.assertEqual(eligible_split("90", 50, None, 2), (Decimal("45.00"), Decimal("45.00")))
    def test_amount_basis(self):
        shares = shares_from_amounts({"A":60,"B":40})
        self.assertEqual(shares["A"], Decimal("60"))
    def test_full_allocation_assertion(self):
        self.assertTrue(assert_fully_allocated("100", ["60", "40"]))
        with self.assertRaises(ValueError): assert_fully_allocated("100", ["60", "39"])
