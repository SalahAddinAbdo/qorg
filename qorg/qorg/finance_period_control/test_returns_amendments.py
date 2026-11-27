from frappe.tests.utils import FrappeTestCase
from qorg.qorg.finance_period_control.returns_amendments import _reverse_capacity
class TestReturnsAmendments(FrappeTestCase):
 def test_reverse_capacity_never_negative(self):
  class E: event_key="E";base_amount=100;amount=100
  class L: entries=[]
  self.assertEqual(_reverse_capacity(L(),E()),100)
