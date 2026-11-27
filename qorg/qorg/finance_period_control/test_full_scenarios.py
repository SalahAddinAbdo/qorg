from frappe.tests.utils import FrappeTestCase
from qorg.qorg.finance_period_control.scenario_matrix import run_matrix
class TestFinanceFullScenarioMatrix(FrappeTestCase):
    def test_all_scenarios(self):self.assertEqual(len(run_matrix()),30)
