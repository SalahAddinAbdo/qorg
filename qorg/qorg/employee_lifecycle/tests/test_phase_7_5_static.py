import ast
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]

def load(slug):
    return json.loads((ROOT/f'qorg/qorg/doctype/{slug}/{slug}.json').read_text())

def test_document_models_cover_requirement_record_and_type():
    for slug in ('employee_document_type','employee_document_requirement','employee_document_record'):
        data=load(slug);assert data['doctype']=='DocType';assert data['name'].startswith('Employee Document')

def test_storage_modes_and_provider_identifiers_exist():
    data=load('employee_document_record');fields={x['fieldname']:x for x in data['fields']}
    options=fields['storage_type']['options']
    for value in ('Frappe Attachment','Microsoft SharePoint / OneDrive','Google Drive','Physical Document','Reference Only'):
        assert value in options
    for name in ('microsoft_drive_id','microsoft_item_id','google_file_id','external_document_id','archive_reference','access_verification_status'):
        assert name in fields

def test_requirements_have_independent_service_blocks():
    fields={x['fieldname'] for x in load('employee_document_requirement')['fields']}
    assert {'blocks_employment','blocks_payroll','blocks_attendance','blocks_leave','blocks_onboarding','blocks_contract'}<=fields

def test_document_engine_integrates_readiness_and_permissions():
    source=(ROOT/'qorg/qorg/employee_lifecycle/documents.py').read_text()
    for token in ('document_service_blockers','apply_document_readiness','evaluate_readiness_with_documents','Microsoft Drive ID','Google Drive File ID','Sensitive documents must use a private File'):
        assert token in source
    permissions=(ROOT/'qorg/qorg/employee_lifecycle/document_permissions.py').read_text()
    assert 'Restricted Medical' in permissions and 'subject_name' in permissions

def test_hooks_register_scheduler_permissions_and_assets():
    source=(ROOT/'qorg/hooks.py').read_text();ast.parse(source)
    for token in ('provision_employee_documents','update_document_statuses','document_permissions.query_condition','employee_documents.js','employee_document_record.js'):
        assert token in source
