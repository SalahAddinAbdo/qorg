import unittest
from qorg.qorg.payroll_workforce_allocation.utils import stable_hash
class TestAllocationMath(unittest.TestCase):
 def test_hash_stable(self): self.assertEqual(stable_hash({"a":1,"b":2}),stable_hash({"b":2,"a":1}))
 def test_percentages(self): self.assertAlmostEqual(1000*60/100+1000*40/100,1000)
