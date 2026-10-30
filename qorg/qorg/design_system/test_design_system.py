import unittest
from qorg.qorg.design_system.service import _hex, css_variables, fingerprint
class TestDesignSystem(unittest.TestCase):
    def test_color(self): self.assertEqual(_hex("#ABC"),"#abc")
    def test_variables_are_namespaced(self): self.assertTrue(all(k.startswith("--qorg-") for k in css_variables({}).keys()))
    def test_fingerprint_is_stable(self): self.assertEqual(fingerprint({"a":1}),fingerprint({"a":1}))
