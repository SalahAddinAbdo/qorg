import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]

def text(path): return (ROOT/path).read_text()

def test_reference_check_doctype_is_standard_and_professional():
    data=json.loads(text('qorg/qorg/doctype/candidate_reference_check/candidate_reference_check.json'))
    assert data['name']=='Candidate Reference Check'
    assert data['module']=='QOrg'
    assert data['autoname']=='naming_series:'
    fields={f['fieldname']:f for f in data['fields']}
    for name in ('job_applicant','job_offer','reference_name','status','result','signed_response','result_rationale'):
        assert name in fields
    assert fields['job_applicant']['options']=='Job Applicant'
    assert fields['job_offer']['options']=='Job Offer'
    assert data['permissions']

def test_reference_check_uses_existing_external_person_references():
    source=text('qorg/qorg/recruitment_extensions/reference_checks.py')
    assert 'person.get("references")' in source
    assert 'reference_source_row' in source
    assert 'External Person' in source

def test_reference_checks_start_after_accepted_offer_and_selected_candidate():
    source=text('qorg/qorg/recruitment_extensions/reference_checks.py')
    assert 'After Offer Acceptance' in source
    assert '_offer_status(job_offer) != "Accepted"' in source
    assert 'qorg_final_decision") != "Selected"' in source

def test_multiple_reference_results_are_independent_and_duplicates_blocked():
    source=text('qorg/qorg/recruitment_extensions/reference_checks.py')
    assert 'Candidate Reference Check' in source
    assert 'An active reference check already exists' in source
    assert 'Satisfactory with Reservations' in source
    assert 'Unsatisfactory' in source

def test_reference_check_settings_are_managed_in_hr_settings():
    rows=json.loads(text('qorg/qorg/recruitment_extensions/data/hr_settings_custom_fields.json'))
    names={r['fieldname'] for r in rows}
    required={
      'qorg_require_reference_checks','qorg_reference_check_trigger',
      'qorg_minimum_required_reference_checks','qorg_require_signed_reference_response',
      'qorg_block_commencement_until_reference_checks','qorg_allow_qualified_reference_result'
    }
    assert required <= names

def test_commencement_is_blocked_by_incomplete_reference_checks():
    source=text('qorg/qorg/recruitment_extensions/reference_checks.py')
    hooks=text('qorg/hooks.py')
    assert 'def validate_commencement_reference_checks' in source
    assert 'Reference checks are incomplete' in source
    assert 'reference_checks.validate_commencement_reference_checks' in hooks

def test_signed_response_and_verification_are_enforced():
    source=text('qorg/qorg/recruitment_extensions/reference_checks.py')
    assert 'require_signed_reference_response' in source
    assert 'Received On and Result are required' in source
    assert 'Result Rationale is required' in source

def test_reference_check_files_are_private():
    source=text('qorg/qorg/people_and_opportunities/private_files.py')
    assert 'Candidate Reference Check' in source
    assert 'doc.is_private = 1' in source

def test_reference_check_email_and_print_format_are_provisioned():
    template='qorg/qorg/recruitment_extensions/data/email_templates/recruitment_-_candidate_reference_check_request_-_bilingual.json'
    data=json.loads(text(template))
    assert data['name']=='Recruitment - Candidate Reference Check Request - Bilingual'
    source=text('qorg/qorg/recruitment_extensions/provisioning.py')
    assert '_reference_check_print_format()' in source
    assert 'Candidate Reference Check Questionnaire - Bilingual' in source
    assert 'Q Universal' in source

def test_applicant_summary_fields_are_read_only():
    rows=json.loads(text('qorg/qorg/recruitment_extensions/data/custom_fields.json'))
    fields={r['fieldname']:r for r in rows if r.get('dt')=='Job Applicant'}
    for name in ('qorg_reference_checks_required','qorg_reference_checks_completed','qorg_reference_check_status','qorg_latest_reference_check_on'):
        assert fields[name]['read_only']==1

def test_runtime_audit_covers_reference_checks():
    source=text('qorg/qorg/recruitment_extensions/acceptance.py')
    assert 'Candidate Reference Check' in source
    assert 'audit_deep_runtime_configuration' in source
    assert 'Recruitment - Candidate Reference Check Request - Bilingual' in source

def test_existing_assessment_reference_check_path_is_preserved():
    rows=json.loads(text('qorg/qorg/recruitment_extensions/data/custom_fields.json'))
    field=next(r for r in rows if r.get('dt')=='Interview Type' and r.get('fieldname')=='qorg_assessment_type')
    assert 'Reference Check' in field['options']
    stage=json.loads(text('qorg/qorg/doctype/recruitment_assessment_stage/recruitment_assessment_stage.json'))
    assessment=next(r for r in stage['fields'] if r['fieldname']=='assessment_type')
    assert 'Reference Check' in assessment['options']


def test_hr_settings_field_rows_match_settings_provisioner_contract():
    rows=json.loads(text('qorg/qorg/recruitment_extensions/data/hr_settings_custom_fields.json'))
    assert all('dt' not in row for row in rows)
    source=text('qorg/qorg/recruitment_extensions/settings_provisioning.py')
    for key in ('qorg_require_reference_checks','qorg_reference_check_trigger','qorg_minimum_required_reference_checks'):
        assert key in source


def test_reference_form_filters_actions_and_dependencies_are_aligned():
    js=text('qorg/qorg/doctype/candidate_reference_check/candidate_reference_check.js')
    data=json.loads(text('qorg/qorg/doctype/candidate_reference_check/candidate_reference_check.json'))
    assert 'qorg_response_status: "Accepted"' in js
    assert 'qorg_final_decision: "Selected"' in js
    assert 'send_reference_check_request' in js
    assert 'record_reference_check_follow_up' in js
    fields={f['fieldname']:f for f in data['fields']}
    assert fields['status']['read_only']==1
    assert fields['result']['mandatory_depends_on']
    assert fields['response_method']['mandatory_depends_on']


def test_reference_email_is_styled_and_questionnaire_is_file_backed():
    email=json.loads(text('qorg/qorg/recruitment_extensions/data/email_templates/recruitment_-_candidate_reference_check_request_-_bilingual.json'))
    assert '#137690' in email['response_html'] and '#cbae66' in email['response_html']
    assert 'confidential' in email['response_html'].lower()
    questionnaire=text('qorg/qorg/recruitment_extensions/templates/candidate_reference_check_questionnaire.html')
    assert 'Employment Verification' in questionnaire
    assert 'Declaration and Signature' in questionnaire
    service=text('qorg/qorg/recruitment_extensions/reference_checks.py')
    assert '_questionnaire_pdf' in service
    assert 'attachments=[_questionnaire_pdf(doc)]' in service


def test_candidate_reference_check_layout_is_balanced_and_sequenced():
    data=json.loads(text('qorg/qorg/doctype/candidate_reference_check/candidate_reference_check.json'))
    fields={row['fieldname']:row for row in data['fields']}
    assert data['field_order']==[row['fieldname'] for row in data['fields']]
    assert len(data['field_order'])==len(set(data['field_order']))
    assert not any(row['fieldtype']=='Page Break' for row in data['fields'])
    for name in (
      'overview_section','reference_section','status_section','tracking_section',
      'response_section','response_details_section','signature_section','communication_section',
    ):
      assert fields[name]['fieldtype']=='Section Break'
    for name in (
      'overview_column_2','reference_column_2','reference_column_3',
      'status_column_2','status_column_3','tracking_column_2','tracking_column_3',
      'response_column_2','response_column_3','signature_column_2',
    ):
      assert fields[name]['fieldtype']=='Column Break'
    assert fields['job_opening']['read_only']==1
    assert fields['external_person']['read_only']==1
    assert fields['company']['read_only']==1
    assert fields['status']['read_only']==1
    assert fields['response_section']['depends_on']
    assert fields['signature_section']['depends_on']
