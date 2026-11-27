import importlib
from frappe.tests.utils import FrappeTestCase
class TestFinanceAcceptance(FrappeTestCase):
 def test_required_modules_import(self):
  modules=("service","legacy_migration","commitment_lifecycle","projection","budget_sync","acceptance")
  for name in modules:self.assertTrue(importlib.import_module(f"qorg.qorg.finance_period_control.{name}"))
