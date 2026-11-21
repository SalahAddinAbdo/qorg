import ast, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class TestV11Contract(unittest.TestCase):
    def test_separated_actions(self):
        source=(ROOT/'lifecycle.py').read_text()
        for action in ('calculate','approve','post','reconcile','close','reverse'):
            self.assertIn(f'def {action}(',source)
    def test_reversal_is_new_document(self):
        source=(ROOT/'posting.py').read_text()
        self.assertIn('frappe.new_doc("Journal Entry")',source)
        self.assertIn('create_reversal_entry',source)
    def test_permissions_are_not_stubbed(self):
        source=(ROOT/'permissions.py').read_text()
        self.assertIn('has_payroll_run_permission',source)
        self.assertIn('1=0',source)
    def test_python_parses(self):
        for path in ROOT.rglob('*.py'): ast.parse(path.read_text(),filename=str(path))
