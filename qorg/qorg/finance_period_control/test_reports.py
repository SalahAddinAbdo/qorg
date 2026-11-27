import importlib
from frappe.tests.utils import FrappeTestCase
class TestFinancePeriodReports(FrappeTestCase):
 def test_report_modules_load(self):
  for module in ("qorg.qorg.report.budget_period_performance.budget_period_performance","qorg.qorg.report.commitment_lifecycle_summary.commitment_lifecycle_summary"): self.assertTrue(importlib.import_module(module).execute)
