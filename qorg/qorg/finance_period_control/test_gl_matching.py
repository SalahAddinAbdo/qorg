from frappe.tests.utils import FrappeTestCase
from qorg.qorg.finance_period_control.actuals import account_clause
class TestGLMatchingPolicy(FrappeTestCase):
 def test_expense_policy(self):self.assertIn("root_type='Expense'",account_clause("Expense Only"))
 def test_acquisition_excludes_cash(self):self.assertIn("Cash",account_clause("Asset Acquisition"))
