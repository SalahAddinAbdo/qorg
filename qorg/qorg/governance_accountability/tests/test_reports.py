import json,ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
def read(p):return (ROOT/p).read_text()
def load(p):return json.loads(read(p))

def test_five_standard_reports_exist_and_reference_new_sources():
 expected={"accountability_case_resolution":"Accountability Case","enterprise_risk_register":"Enterprise Risk","compliance_status":"Compliance Obligation","assurance_findings":"Assurance Finding","corrective_action_tracking":"Corrective Action"}
 for slug,dt in expected.items():
  data=load(f"qorg/qorg/report/{slug}/{slug}.json");assert data['ref_doctype']==dt and data['report_type']=='Script Report' and data['module']=='QOrg';assert (ROOT/f"qorg/qorg/report/{slug}/{slug}.py").exists();assert (ROOT/f"qorg/qorg/report/{slug}/{slug}.js").exists()
def test_legacy_complaint_report_reads_unified_accountability_source():
 data=load('qorg/qorg/report/complaint_resolution/complaint_resolution.json');assert data['ref_doctype']=='Accountability Case'
 assert 'accountability_case_resolution' in read('qorg/qorg/report/complaint_resolution/complaint_resolution.py')
def test_public_submission_uses_post_random_token_and_hash_only():
 s=read('qorg/qorg/governance_accountability/portal.py');assert '@frappe.whitelist(allow_guest=True,methods=["POST"])' in s;assert 'secrets.token_urlsafe(32)' in s;assert 'hashlib.sha256' in s;assert 'external_tracking_key_hash' in s
def test_tracking_uses_constant_time_comparison_and_minimal_output():
 s=read('qorg/qorg/governance_accountability/portal.py');assert 'secrets.compare_digest' in s;assert 'case_details' not in s[s.index('def track_accountability_case'):];assert 'responses[-3:]' in s
def test_anonymous_public_submission_does_not_store_identity_or_contact():
 s=read('qorg/qorg/governance_accountability/portal.py');assert 'reporter_name":None if anonymous' in s;assert 'email":None if anonymous' in s;assert 'mobile_no":None if anonymous' in s
def test_notifications_require_consent_and_hide_sensitive_subjects():
 s=read('qorg/qorg/governance_accountability/notifications.py');assert 'doc.anonymous or not doc.consent_to_contact' in s;assert 'Confidential case' in s;assert 'details_hidden' in s
def test_bilingual_templates_use_application_brand_colors_and_no_case_details():
 data=load('qorg/qorg/governance_accountability/data/email_templates/accountability_templates.json');assert len(data)==4
 for row in data:
  assert row['doctype']=='Email Template';assert '#137690' in row['response_html'] and '#cbae66' in row['response_html'];assert 'case_details' not in row['response_html']
def test_provisioning_creates_or_adopts_templates_without_overwriting():
 s=read('qorg/qorg/governance_accountability/provisioning.py');assert '_provision_email_templates(result)' in s;assert 'frappe.db.exists("Email Template",name)' in s;assert 'frappe.get_doc(data).insert(ignore_permissions=True)' in s
def test_report_and_portal_sources_parse():
 for folder in ('qorg/qorg/governance_accountability','qorg/qorg/report/accountability_case_resolution','qorg/qorg/report/enterprise_risk_register','qorg/qorg/report/compliance_status','qorg/qorg/report/assurance_findings','qorg/qorg/report/corrective_action_tracking'):
  for p in (ROOT/folder).rglob('*.py'):ast.parse(p.read_text())
