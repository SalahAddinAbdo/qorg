import ast,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class TestV24(unittest.TestCase):
 def test_parse(self):
  for p in ROOT.glob("*.py"):ast.parse(p.read_text(),filename=str(p))
 def test_liability_modes(self):
  s=(ROOT/"liabilities.py").read_text()
  for x in ("Split Statutory Liabilities","Split Selected Liabilities","Split All Payroll Liabilities","resolve_liability_rules","resolve_liability_basis","validate_payment_dimensions","reconcile_liability_payment"):self.assertIn(x,s)
 def test_payment_hooks(self):
  s=(ROOT.parents[1]/"hooks.py").read_text()
  for x in ("payment.validate_payment_entry","payment.payment_entry_on_submit","payment.payment_entry_on_cancel"):self.assertIn(x,s)
 def test_reconciliation_child(self):
  p=ROOT.parent/"doctype"/"payroll_reconciliation_detail"/"payroll_reconciliation_detail.json";self.assertTrue(p.exists());self.assertTrue(json.loads(p.read_text())["istable"])
 def test_run_fields(self):
  p=ROOT.parent/"doctype"/"payroll_allocation_run"/"payroll_allocation_run.json";fields={x["fieldname"] for x in json.loads(p.read_text())["fields"]};self.assertTrue({"reconciliation_details","liability_reconciliation_status","payment_reconciliation_status","reconciled_by","reconciled_on","closed_by","closed_on"}.issubset(fields))
 def test_dimension_key(self):self.assertIn("GL_DIMENSION_DIFFERENCE",(ROOT/"reconciliation.py").read_text())
if __name__=="__main__":unittest.main()
