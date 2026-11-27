from frappe.tests.utils import FrappeTestCase
from qorg.qorg.finance_period_control.amount_policy import _nonrecoverable
class TestAmountPolicy(FrappeTestCase):
 def test_valuation_tax_is_cost(self):self.assertTrue(_nonrecoverable({"category":"Valuation"}))
 def test_recoverable_total_tax_excluded(self):self.assertFalse(_nonrecoverable({"category":"Total","is_recoverable":1}))
