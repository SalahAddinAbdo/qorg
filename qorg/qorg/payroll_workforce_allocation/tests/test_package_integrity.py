import json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
class TestPackageIntegrity(unittest.TestCase):
 def test_doctypes_exist(self):
  for slug in ("workforce_funding_plan","workforce_funding_destination","payroll_cost_policy","payroll_component_rule","payroll_allocation_run","payroll_allocation_result","payroll_allocation_exception","payroll_liability_rule"):
   self.assertTrue((ROOT/"doctype"/slug/f"{slug}.json").exists())
 def test_json(self):
  for p in ROOT.rglob("*.json"): json.loads(p.read_text())
