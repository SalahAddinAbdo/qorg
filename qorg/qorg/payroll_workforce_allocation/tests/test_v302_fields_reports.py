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
  report_root = BASE / "qorg/report"
  reports = (
   "payroll_readiness",
   "payroll_control_summary",
   "payroll_reconciliation",
   "payroll_allocation_by_project_and_funding",
   "unallocated_and_ineligible_payroll_cost",
   "payroll_liability_reconciliation",
  )
  for report in reports:
   report_dir = report_root / report
   py_path = report_dir / f"{report}.py"
   js_path = report_dir / f"{report}.js"
   json_path = report_dir / f"{report}.json"
   self.assertTrue(py_path.exists(), f"Missing report Python: {py_path}")
   self.assertTrue(js_path.exists(), f"Missing report JavaScript: {js_path}")
   self.assertTrue(json_path.exists(), f"Missing report metadata: {json_path}")
   source = py_path.read_text(encoding="utf-8")
   self.assertIn("summary", source, f"Missing summary in {py_path}")
   self.assertIn("col(", source, f"Missing col helper in {py_path}")
   self.assertIn(
    "payrollSticky",
    js_path.read_text(encoding="utf-8"),
    f"Missing payrollSticky in {js_path}",
   )
   metadata = json.loads(json_path.read_text(encoding="utf-8"))
   self.assertIn(
    "prepared_report",
    metadata,
    f"Missing prepared_report in {json_path}",
   )
 def test_setting_effects(self):
  self.assertIn("custom_require_full_payroll_allocation",(ROOT/"lifecycle.py").read_text());self.assertIn("custom_enforce_liability_dimensions_on_payment",(ROOT/"liabilities.py").read_text());self.assertIn("custom_payroll_allocation_rounding_account",(ROOT/"posting.py").read_text())
if __name__=="__main__":unittest.main()
