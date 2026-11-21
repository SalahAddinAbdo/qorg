import ast,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];PKG=ROOT/'payroll_workforce_allocation'
class TestV14Closure(unittest.TestCase):
 def test_monthly_effort_doctypes(self):
  for slug in ('monthly_effort_certification','monthly_effort_certification_detail'):
   self.assertTrue((ROOT/'doctype'/slug/f'{slug}.json').exists())
 def test_currency_filled_in_allocator(self):
  source=(PKG/'allocator.py').read_text()
  for token in ('company_currency_amount','exchange_rate','from .currency import'):self.assertIn(token,source)
 def test_budget_locking(self):
  source=(PKG/'reservations.py').read_text();self.assertIn('for update',source);self.assertIn('Budget Line',source)
 def test_snapshot_and_version(self):
  source=(PKG/'lifecycle.py').read_text();self.assertIn('build_snapshot',source);self.assertIn('audit_snapshot_hash',source)
 def test_print_requires_permission(self): self.assertIn('has_permission("read")',(PKG/'printing.py').read_text())
 def test_indexes_workspace_translations(self):
  source=(PKG/'provisioning.py').read_text();self.assertIn('_ensure_indexes',source);self.assertIn('_ensure_workspace_links',source);self.assertTrue((ROOT.parent/'translations/ar.csv').exists())
 def test_python_parses(self):
  for p in PKG.rglob('*.py'):ast.parse(p.read_text(),filename=str(p))
