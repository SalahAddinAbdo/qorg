import ast
import json
import unittest
from pathlib import Path
MODULE_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = MODULE_ROOT / "payroll_workforce_allocation"
APP_ROOT = Path(__file__).resolve().parents[3]

class TestSourceContract(unittest.TestCase):
    def test_all_python_files_parse(self):
        for path in PACKAGE_ROOT.rglob("*.py"):
            ast.parse(path.read_text(), filename=str(path))

    def test_six_reports_exist(self):
        reports = ["payroll_readiness", "payroll_control_summary", "payroll_reconciliation", "payroll_allocation_by_project_and_funding", "unallocated_and_ineligible_payroll_cost", "payroll_liability_reconciliation"]
        for report in reports:
            self.assertTrue((MODULE_ROOT / "report" / report / f"{report}.json").exists())

    def test_hooks_and_patch_registered(self):
        hooks = (APP_ROOT / "hooks.py").read_text()
        patches = (APP_ROOT / "patches.txt").read_text()
        self.assertIn("payroll_workforce_allocation.migration.migrate", hooks)
        self.assertIn("payroll_allocation_salary_slip.js", hooks)
        self.assertIn("provision_payroll_workforce_allocation", patches)

    def test_no_automatic_project_creation(self):
        source = "\n".join(path.read_text() for path in PACKAGE_ROOT.glob("*.py"))
        self.assertNotIn('frappe.new_doc("Project")', source)
        self.assertNotIn('frappe.new_doc("Funding Agreement")', source)
        self.assertNotIn('frappe.new_doc("Budget Line")', source)
