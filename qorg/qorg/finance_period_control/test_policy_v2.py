from frappe.tests.utils import FrappeTestCase
class TestPolicyV2(FrappeTestCase):
 def test_module_imports(self):
  from qorg.qorg.finance_period_control import policy_v2,period_factory,cross_period
  self.assertTrue(policy_v2 and period_factory and cross_period)
