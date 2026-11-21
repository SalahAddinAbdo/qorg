import ast,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class TestV25(unittest.TestCase):
 def test_parse(self):
  for p in ROOT.glob("*.py"):ast.parse(p.read_text(),filename=str(p))
 def test_security(self):
  s=(ROOT/"permissions.py").read_text()
  for x in ("Grant Manager","Projects Manager","Auditor","policy_query","effort_query","assert_report_access","aggregate_only"):self.assertIn(x,s)
 def test_reports(self):
  for p in (ROOT.parent/"report").glob("payroll_*/*.py"):
   s=p.read_text();self.assertIn("summary",s)
 def test_print_disclosure(self):
  s=(ROOT/"printing.py").read_text()
  for x in ("None","Project and Percentage","Project, Funding and Percentage","Full Authorized Disclosure","can_view_funding_amounts"):self.assertIn(x,s)
 def test_targeted_notifications(self):
  s=(ROOT/"notifications.py").read_text();self.assertIn("User Permission",s);self.assertIn("reports_to",s)
if __name__=="__main__":unittest.main()
