from frappe.tests.utils import FrappeTestCase
from qorg.qorg.finance_period_control.projection import _period_allocation
class TestBudgetLineProjection(FrappeTestCase):
    def test_period_allocation_is_isolated(self):
        class R:
            def __init__(self,p,a):self.budget_period=p;self.allocated_amount=a
        class L:
            def get(self,k):return [R("P1",10),R("P2",20)]
        self.assertEqual(_period_allocation(L(),"P1"),10)
