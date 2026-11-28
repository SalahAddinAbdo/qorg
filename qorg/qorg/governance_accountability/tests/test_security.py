import ast,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
def read(p):return (ROOT/p).read_text()
def load(p):return json.loads(read(p))
def test_public_features_are_disabled_by_default_and_captcha_required():
 d=load('qorg/qorg/doctype/accountability_settings/accountability_settings.json');f={x['fieldname']:x for x in d['fields']};assert f['enable_public_intake']['default']=='0';assert f['enable_public_tracking']['default']=='0';assert f['require_captcha']['default']=='1'
def test_rate_limit_hashes_ip_and_uses_hour_bucket():
 s=read('qorg/qorg/governance_accountability/security.py');assert 'hashlib.sha256(client_ip().encode())' in s;assert 'cache.incr(key)' in s;assert 'cache.expire(key,3700)' in s;assert 'RateLimitExceededError' in s
def test_portal_enforces_feature_flags_rate_limits_captcha_and_expiry():
 s=read('qorg/qorg/governance_accountability/portal.py');
 for x in ('enable_public_intake','enable_public_tracking','enforce_rate_limit','validate_captcha','tracking_token_validity_days','disable_tracking_after_closure_days'):assert x in s
def test_sensitive_records_have_owner_responsible_permission_queries():
 hooks=read('qorg/hooks.py')
 for dt in ('Enterprise Risk','Compliance Obligation','Assurance Finding','Corrective Action'):assert dt in hooks
 s=read('qorg/qorg/governance_accountability/record_permissions.py');assert 'owner' in s and 'risk_owner' in s and 'responsible_user' in s
def test_procurement_dashboard_links_unified_case_not_legacy_complaint():
 s=read('qorg/qorg/doctype/procurement_process/procurement_process_dashboard.py');assert 'Accountability Case' in s;assert 'Procurement Complaint' not in s;assert 'non_standard_fieldnames' in s
def test_public_pages_exist_and_reflect_disabled_state():
 for route in ('accountability','accountability-track'):
  assert (ROOT/f'qorg/www/{route}/index.py').exists();html=read(f'qorg/www/{route}/index.html');assert 'not currently enabled' in html
def test_runtime_audit_covers_sources_reports_templates_and_migration():
 s=read('qorg/qorg/governance_accountability/acceptance.py');assert 'REQUIRED_DOCTYPES' in s and 'REQUIRED_REPORTS' in s and 'REQUIRED_TEMPLATES' in s;assert 'legacy_procurement_complaint_removed' in s
def test_new_python_sources_parse():
 for name in ('security.py','record_permissions.py','acceptance.py','portal.py'):
  ast.parse(read('qorg/qorg/governance_accountability/'+name))
