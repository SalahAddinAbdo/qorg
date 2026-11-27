from frappe.tests.utils import FrappeTestCase
from qorg.qorg.finance_period_control.routing_v2 import _po_linked,_pi_linked
class TestRoutingV2(FrappeTestCase):
 def test_mixed_row_detection(self):
  class R:
   def __init__(self,**kw):self.kw=kw
   def get(self,k):return self.kw.get(k)
  self.assertTrue(_po_linked(R(material_request_item="MRI-1")))
  self.assertFalse(_po_linked(R()))
  self.assertTrue(_pi_linked(R(po_detail="POI-1")))
