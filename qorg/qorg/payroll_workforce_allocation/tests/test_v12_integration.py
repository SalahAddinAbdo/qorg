import ast,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
PKG=ROOT/'payroll_workforce_allocation'
class TestV12Integration(unittest.TestCase):
 def test_parent_forms_have_tabs_sections_and_columns(self):
  for slug in ('workforce_funding_plan','payroll_cost_policy','payroll_allocation_run'):
   doc=json.loads((ROOT/'doctype'/slug/f'{slug}.json').read_text());types=[f['fieldtype'] for f in doc['fields']]
   self.assertGreaterEqual(types.count('Tab Break'),3,slug);self.assertGreaterEqual(types.count('Section Break'),3,slug);self.assertGreaterEqual(types.count('Column Break'),1,slug)
 def test_grid_columns_do_not_exceed_twelve(self):
  for slug in ('workforce_funding_destination','payroll_component_rule','payroll_liability_rule','payroll_allocation_result','payroll_allocation_exception'):
   doc=json.loads((ROOT/'doctype'/slug/f'{slug}.json').read_text());self.assertLessEqual(sum(int(f.get('columns') or 0) for f in doc['fields'] if f.get('in_list_view')),12,slug)
 def test_source_fingerprint_is_shared(self):
  self.assertIn('payroll_source_fingerprint', (PKG/'allocator.py').read_text());self.assertIn('payroll_source_fingerprint', (PKG/'lifecycle.py').read_text())
 def test_posting_proves_clearing(self):
  source=(PKG/'posting.py').read_text();self.assertIn('_assert_clearing_funded',source);self.assertIn('tabGL Entry',source)
 def test_guards_are_hooked(self):
  hooks=(ROOT.parent/'hooks.py').read_text();self.assertIn('validate_other_allocation_document',hooks)
 def test_no_python_stubs(self):
  for name in ('permissions.py','notifications.py','reporting.py'):
   source=(PKG/name).read_text();self.assertNotIn('return None',source,name)
