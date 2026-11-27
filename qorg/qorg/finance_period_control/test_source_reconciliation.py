from frappe.tests.utils import FrappeTestCase
from qorg.qorg.finance_period_control.source_reconciliation import event_key
from qorg.qorg.finance_period_control.actuals import account_clause
class TestSourceReconciliation(FrappeTestCase):
 def test_row_key_distinguishes_rows(self):self.assertNotEqual(event_key("Purchase Order","PO-1","R1","Ordered","Increase"),event_key("Purchase Order","PO-1","R2","Ordered","Increase"))
 def test_asset_policy_excludes_cash_and_receivable(self):
  clause=account_clause("Asset Acquisition");self.assertIn("Cash",clause);self.assertIn("Receivable",clause)
