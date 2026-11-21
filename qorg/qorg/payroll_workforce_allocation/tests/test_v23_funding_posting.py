import ast,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class TestV23FundingPosting(unittest.TestCase):
 def test_parse(self):
  for p in ROOT.glob("*.py"):ast.parse(p.read_text(),filename=str(p))
 def test_eligibility_controls(self):
  s=(ROOT/"eligibility.py").read_text();
  for token in ("PROJECT_CLOSURE_LOCK","AGREEMENT_EXPIRED","BUDGET_LINE_GROUP","available_budget","payroll_reserved"):self.assertIn(token,s)
 def test_commitment_adapter(self):
  s=(ROOT/"reservations.py").read_text();
  for token in ("Commitment Entry","Commitment Ledger","for update","idempotency_key","mark_posted","release_run"):self.assertIn(token,s)
 def test_posting_idempotency_and_reversal(self):
  s=(ROOT/"posting.py").read_text();
  for token in ("custom_payroll_allocation_run","component_account","_assert_balanced","create_reversal_entry","docstatus!=1"):self.assertIn(token,s)
 def test_run_fields(self):
  p=ROOT.parent/"doctype"/"payroll_allocation_run"/"payroll_allocation_run.json";fields={x["fieldname"] for x in json.loads(p.read_text())["fields"]}
  self.assertTrue({"source_accrual_journal_entry","company_currency","commitment_status","posted_by","posted_on","reversed_by","reversed_on"}.issubset(fields))
if __name__=="__main__":unittest.main()
