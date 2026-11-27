from frappe.tests.utils import FrappeTestCase
class TestDistributionBridge(FrappeTestCase):
 def test_phase_module_imports(self):
  from qorg.qorg.finance_period_control import distribution_bridge
  self.assertTrue(distribution_bridge.TABLE_FIELD)
