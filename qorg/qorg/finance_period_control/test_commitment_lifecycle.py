from types import SimpleNamespace
from unittest.mock import patch
from frappe.tests.utils import FrappeTestCase
from qorg.qorg.finance_period_control.commitment_lifecycle import make_event_key
class TestCommitmentLifecycle(FrappeTestCase):
    def test_event_key_is_deterministic(self):
        self.assertEqual(make_event_key("Purchase Order","PO-1","Ordered","Increase","ROW-1"),"Purchase Order|PO-1|ROW-1|Ordered|Increase")
