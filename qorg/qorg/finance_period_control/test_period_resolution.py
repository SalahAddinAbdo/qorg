from unittest.mock import patch, MagicMock
from frappe.tests.utils import FrappeTestCase
from qorg.qorg.finance_period_control.service import resolve_budget_period

class TestPeriodResolution(FrappeTestCase):
    @patch("qorg.qorg.finance_period_control.service._period")
    def test_explicit_has_highest_precedence(self, period):
        period.return_value=MagicMock(name="FY-25")
        _,source=resolve_budget_period("ACME","2025-01-15",explicit="FY-25")
        self.assertEqual(source,"Explicit")
        period.assert_called_once_with("FY-25","ACME",period.call_args.args[2],True)
