from frappe.tests.utils import FrappeTestCase
class TestCrossPeriod(FrappeTestCase):
 def test_module_imports(self):
  from qorg.qorg.finance_period_control import cross_period
  self.assertTrue(cross_period.EPSILON)
