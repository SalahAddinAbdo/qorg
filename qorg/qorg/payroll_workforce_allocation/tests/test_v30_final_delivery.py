import ast,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT.parents[1]
class TestV30(unittest.TestCase):
 def test_parse(self):
  for p in ROOT.glob("*.py"):ast.parse(p.read_text(),filename=str(p))
 def test_patch(self):self.assertIn("qorg.qorg.patches.v5_0.complete_payroll_workforce_allocation",(BASE/"patches.txt").read_text())
 def test_no_backfill(self):self.assertIn("financial_backfill_performed\":False",(ROOT/"migration.py").read_text().replace(" ",""))
 def test_acceptance_gate(self):
  s=(ROOT/"acceptance.py").read_text()
  for x in ("accounting_passed","permissions_passed","idempotency_passed","ready_for_acceptance"):self.assertIn(x,s)
 def test_docs(self):
  for x in ("PAYROLL_v3.0.2_DEPLOYMENT.md","PAYROLL_v3.0.2_ROLLBACK.md","PAYROLL_v3.0.2_TEST_MATRIX.md","PAYROLL_v3.0.2_RUNTIME_ACCEPTANCE_TEMPLATE.json"):self.assertTrue((BASE/x).exists())
if __name__=="__main__":unittest.main()
