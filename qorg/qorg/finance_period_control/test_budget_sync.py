from frappe.tests.utils import FrappeTestCase
from qorg.qorg.finance_period_control.budget_sync import _sync_key,_digest
class TestERPNextBudgetSync(FrappeTestCase):
 def test_sync_key_is_stable(self):self.assertEqual(_sync_key("ACME","2025","P1"),"QORG|ACME|2025|Project|P1")
 def test_digest_is_order_stable(self):self.assertEqual(_digest([{"account":"A","budget_amount":1}]),_digest([{"budget_amount":1,"account":"A"}]))
