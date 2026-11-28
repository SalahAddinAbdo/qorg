import ast
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]

def read(path): return (ROOT/path).read_text()

def load(path): return json.loads(read(path))

def test_accountability_case_is_standard_and_uses_existing_responsibility_fields():
    data=load('qorg/qorg/doctype/accountability_case/accountability_case.json')
    assert data['name']=='Accountability Case'
    assert data['module']=='QOrg'
    assert data['autoname']=='naming_series:'
    fields={row['fieldname']:row for row in data['fields']}
    for name in ('custom_current_responsible_user','custom_previous_responsible_user','referrals','follow_ups','response_logs'):
        assert name in fields
    assert fields['referrals']['options']=='Accountability Referral'
    assert fields['follow_ups']['cannot_add_rows']==1
    assert fields['response_logs']['cannot_delete_rows']==1

def test_routing_is_subject_context_and_sensitivity_driven():
    source=read('qorg/qorg/governance_accountability/routing.py')
    for field in ('company','case_type','category','stakeholder_type','project','department','channel','severity','confidentiality','related_doctype'):
        assert f'"{field}"' in source
    assert 'priority asc' in source
    assert '_rule_specificity' in source
    assert 'Ambiguous accountability routing rules' in source

def test_routing_occurs_at_triage_not_registration():
    validation=read('qorg/qorg/governance_accountability/validations.py')
    actions=read('qorg/qorg/governance_accountability/actions.py')
    assert 'apply_routing(doc' not in validation
    assert 'apply_routing(doc, require_match=True)' in actions
    assert '_apply_initial_sla' in validation

def test_anonymous_intake_minimizes_personal_data():
    source=read('qorg/qorg/governance_accountability/validations.py')
    assert 'doc.set(field,None)' in source
    for field in ('reporter_name','email','mobile_no','employee','external_person','supplier','contact'):
        assert f'"{field}"' in source
    assert 'doc.consent_to_contact=0' in source

def test_sensitive_cases_are_restricted_beyond_receiving_role():
    source=read('qorg/qorg/governance_accountability/permissions.py')
    assert 'Confidential' in source and 'Highly Confidential' in source
    assert 'confidentiality` in (\'Standard\',\'Restricted\')' in source
    assert 'Accountability Manager' in source

def test_protected_attachments_are_private_and_not_movable_without_write_access():
    source=read('qorg/qorg/governance_accountability/private_files.py')
    assert 'doc.is_private=1' in source
    assert 'Write permission is required on both records' in source
    assert 'Accountability Case' in source

def test_case_actions_enforce_sequence_and_create_audit_rows():
    source=read('qorg/qorg/governance_accountability/actions.py')
    for fn in ('acknowledge_case','triage_case','assign_case','accept_referral','return_referral','add_follow_up','add_response','close_case','reopen_case'):
        assert f'def {fn}' in source
    assert 'doc.append("referrals"' in source
    assert 'doc.append("follow_ups"' in source
    assert 'doc.append("response_logs"' in source

def test_procurement_context_is_limited_to_relevant_categories():
    source=read('qorg/qorg/governance_accountability/validations.py')
    assert 'Procurement Process requires a procurement' in source
    assert 'Supplier Performance' in source
    assert 'Fraud and Corruption' in source

def test_hooks_register_permissions_and_private_files_once_in_checkpoint_source():
    hooks=read('qorg/hooks.py')
    for marker in ('governance_accountability.permissions.accountability_case_query','governance_accountability.permissions.accountability_case_permission','governance_accountability.private_files.has_file_permission','governance_accountability.private_files.validate_private_file'):
        assert hooks.count(marker)==1

def test_python_sources_parse():
    for path in (ROOT/'qorg/qorg/governance_accountability').rglob('*.py'):
        ast.parse(path.read_text())
