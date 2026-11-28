import ast,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
def read(p):return (ROOT/p).read_text()
def load(p):return json.loads(read(p))
def test_all_grc_permission_queries_have_matching_has_permission_hooks():
 h=read('qorg/hooks.py')
 for dt in ('Accountability Case','Investigation Case','Enterprise Risk','Compliance Obligation','Assurance Finding','Corrective Action'):
  assert h.count(f'"{dt}"')>=2
def test_tracking_expiry_uses_created_timestamp_not_migration_timestamp():
 p=read('qorg/qorg/governance_accountability/portal.py'); assert 'external_tracking_created_on' in p; assert 'token_created_on=doc.external_tracking_created_on or doc.creation' in p
 meta=load('qorg/qorg/doctype/accountability_case/accountability_case.json'); assert 'external_tracking_created_on' in [x['fieldname'] for x in meta['fields']]
def test_legacy_source_is_retired_and_public_tracking_remains_disabled_by_default():
 assert not (ROOT/'qorg/qorg/governance_accountability/migration.py').exists()
 settings=read('qorg/qorg/doctype/accountability_settings/accountability_settings.json')
 assert '"enable_public_tracking": 0' in settings or '"default": "0"' in settings

def test_workspace_has_standard_export_metadata():
 w=load('qorg/qorg/workspace/governance_accountability/governance_accountability.json')
 for key in ('docstatus','idx','for_user','hide_custom','parent_page','type'): assert key in w
 assert w['parent_page']=='Q Management Hub' and w['type']=='Workspace'
def test_runtime_smoke_api_covers_workspace_imports_and_doctypes():
 s=read('qorg/qorg/governance_accountability/runtime_tests.py')
 for value in ('Governance Accountability','audit_deep_runtime_configuration','migrate_procurement_complaints','run_daily_retention_jobs'):assert value in s
 ast.parse(s)
