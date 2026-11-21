import ast,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT.parents[1]
class TestV302(unittest.TestCase):
 def test_parse(self):
  for p in ROOT.glob("*.py"):ast.parse(p.read_text(),filename=str(p))
 def test_company_layout(self):
  s=(ROOT/"provisioning.py").read_text();self.assertIn("custom_payroll_allocation_column_2",s);self.assertIn("custom_payroll_liability_section",s);self.assertIn("custom_payroll_liability_column_2",s)
 def test_standard_layout(self):
  s=(ROOT/"provisioning.py").read_text();self.assertIn("custom_payroll_control_section",s);self.assertIn("custom_payroll_allocation_summary_section",s)
 def test_reconciliation_layout(self):
  d=json.loads((BASE/"qorg/doctype/payroll_reconciliation_detail/payroll_reconciliation_detail.json").read_text());self.assertGreaterEqual(sum(x["fieldtype"]=="Section Break" for x in d["fields"]),3);self.assertGreaterEqual(sum(x["fieldtype"]=="Column Break" for x in d["fields"]),3)
 def test_reports(self):
  for p in (BASE/"qorg/report").glob("*/*.py"):
   s=p.read_text();self.assertIn("summary",s);self.assertIn("col(",s)
  for p in (BASE/"qorg/report").glob("*/*.js"):self.assertIn("payrollSticky",p.read_text())
  for p in (BASE/"qorg/report").glob("*/*.json"):
   d=json.loads(p.read_text());self.assertIn("prepared_report",d)
 def test_setting_effects(self):
  self.assertIn("custom_require_full_payroll_allocation",(ROOT/"lifecycle.py").read_text());self.assertIn("custom_enforce_liability_dimensions_on_payment",(ROOT/"liabilities.py").read_text());self.assertIn("custom_payroll_allocation_rounding_account",(ROOT/"posting.py").read_text())
if __name__=="__main__":unittest.main()
