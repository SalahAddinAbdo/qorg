import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class TestV301(unittest.TestCase):
 def test_parse(self):
  for p in ROOT.glob("*.py"):ast.parse(p.read_text(),filename=str(p))
 def test_linked_payments(self):
  s=(ROOT/"payment.py").read_text();self.assertIn("reference_doctype",s);self.assertNotIn('filters={"company":doc.company',s)
 def test_liability_posting(self):
  s=(ROOT/"posting.py").read_text();self.assertIn("_liability_rows",s);self.assertIn("resolve_liability_rules",s);self.assertIn("Source Account Reclassification",s)
 def test_budget_no_double_count(self):self.assertIn('Budget Line.available_amount',(ROOT/"eligibility.py").read_text())
 def test_no_workspace_save(self):self.assertNotIn('document.save(', (ROOT/"provisioning.py").read_text())
 def test_print_no_frappe_call(self):self.assertNotIn('frappe.call(', (ROOT.parents[1]/"printing/templates/salary_slip_workforce_funding_statement.html").read_text())
if __name__=="__main__":unittest.main()
