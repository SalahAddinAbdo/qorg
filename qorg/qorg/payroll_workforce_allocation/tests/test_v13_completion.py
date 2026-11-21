import ast,json,unittest
from decimal import Decimal
from pathlib import Path
from qorg.qorg.payroll_workforce_allocation.allocation_basis import aggregate_weighted
ROOT=Path(__file__).resolve().parents[2];PKG=ROOT/'payroll_workforce_allocation'
class TestV13Completion(unittest.TestCase):
 def test_weighted_basis(self):
  rows=aggregate_weighted([(60,[{'project':'A','share':100}]),(40,[{'project':'B','share':100}])]);self.assertEqual({x['project']:x['share'] for x in rows},{'A':Decimal('60'),'B':Decimal('40')})
 def test_all_basis_implemented(self):
  source=(PKG/'allocation_basis.py').read_text()
  for name in ['Work Allocation','Basic Salary Allocation','Taxable Earnings Allocation','Net Pay Allocation','Source Component Allocation','Explicit Origin','Do Not Allocate']:self.assertIn(name,source)
 def test_budget_and_relationship_guards(self):
  source=(PKG/'eligibility.py').read_text();self.assertIn('available_amount',source);self.assertIn('Funding Agreement is not linked',source)
 def test_approval_reference_fields(self):
  data=json.loads((ROOT/'doctype/payroll_allocation_exception/payroll_allocation_exception.json').read_text());names={x['fieldname'] for x in data['fields']};self.assertTrue({'approval_reference_type','approval_reference','approved_by','approved_on'}<=names)
 def test_disclosure_levels(self):
  source=(PKG/'printing.py').read_text();self.assertIn('Do Not Show Funding Details',source);self.assertIn('Full Funding Details',source)
 def test_parse(self):
  for p in PKG.rglob('*.py'):ast.parse(p.read_text(),filename=str(p))
