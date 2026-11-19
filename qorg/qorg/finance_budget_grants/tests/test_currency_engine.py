import unittest
from unittest.mock import patch
from qorg.qorg.finance_budget_grants.currency import convert,quantize,resolve_exchange_rate
class TestCurrencyEngine(unittest.TestCase):
 def test_same_currency(self):self.assertEqual(resolve_exchange_rate("USD","USD","2026-01-01").rate,1)
 def test_manual_rate_requires_approval(self):
  with self.assertRaises(Exception):resolve_exchange_rate("USD","YER","2026-01-01","Manual Approved",250)
 def test_precision_rounding(self):self.assertEqual(quantize(1.005,2),1.01)
 def test_convert(self):self.assertEqual(convert(10,2.5,2),25)
