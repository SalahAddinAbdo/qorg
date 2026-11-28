import json,ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
def read(p):return (ROOT/p).read_text()
def load(p):return json.loads(read(p))
def test_workspace_links_all_primary_records_reports_and_settings():
 d=load('qorg/qorg/workspace/governance_accountability/governance_accountability.json')
 assert d['module']=='QOrg' and d['public']==1
 text=json.dumps(d)
 for name in ('Accountability Case','Investigation Case','Corrective Action','Enterprise Risk','Compliance Obligation','Assurance Finding','Accountability Settings'):assert name in text
def test_retention_disables_tokens_and_minimizes_contact_without_deleting_cases():
 s=read('qorg/qorg/governance_accountability/retention.py')
 assert 'external_tracking_enabled": 0' in s and 'external_tracking_key_hash": None' in s
 for field in ('email','mobile_no','employee','external_person','supplier','contact'):assert f'"{field}": None' in s
 assert '.delete(' not in s and 'delete_doc' not in s
def test_daily_scheduler_registers_retention_job_once():
 hooks=read('qorg/hooks.py');assert hooks.count('governance_accountability.retention.run_daily_retention_jobs')==1
def test_company_scope_uses_standard_user_permission():
 s=read('qorg/qorg/governance_accountability/record_permissions.py');assert 'User Permission' in s and '"allow": "Company"' in s and 'applicable_for' in s
def test_retention_source_parses():ast.parse(read('qorg/qorg/governance_accountability/retention.py'))
