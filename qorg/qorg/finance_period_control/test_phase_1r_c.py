from frappe.tests.utils import FrappeTestCase
from qorg.qorg.finance_period_control.actuals import account_clause
class TestPhase1RC(FrappeTestCase):
 def test_asset_clause_is_restricted(self):
  clause=account_clause("Asset Acquisition");self.assertIn("Fixed Asset",clause);self.assertNotIn("Receivable",clause)
