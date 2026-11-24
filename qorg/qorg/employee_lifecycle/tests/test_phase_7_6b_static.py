import ast
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]

def load(slug):
    return json.loads((ROOT/f'qorg/qorg/doctype/{slug}/{slug}.json').read_text())

def test_only_approved_gap_models_are_created():
    expected={
        'Training Need Request','Training Need Participant','Development Action'
    }
    actual={load(slug)['name'] for slug in ('training_need_request','training_need_participant','development_action')}
    assert actual==expected
    for forbidden in ('Training Program','Training Event','Appraisal','Employee Skill Map'):
        assert not (ROOT/f'qorg/qorg/doctype/{frappe_slug(forbidden)}').exists()

def frappe_slug(name): return name.lower().replace(' ','_')

def test_training_need_has_scope_funding_and_conversion_controls():
    fields={f['fieldname']:f for f in load('training_need_request')['fields']}
    for name in ('request_scope','need_source','participants','funding_required','project','cost_center','funding_agreement','budget_line','training_program','training_event','conversion_snapshot'):
        assert name in fields
    assert fields['participants']['options']=='Training Need Participant'
    assert fields['status']['read_only']==1
    assert fields['project']['options']=='Project'

def test_development_action_uses_dynamic_source_and_document_evidence():
    fields={f['fieldname']:f for f in load('development_action')['fields']}
    assert fields['source_document']['fieldtype']=='Dynamic Link'
    assert fields['source_document']['options']=='source_doctype'
    assert fields['completion_document']['options']=='Employee Document Record'
    assert fields['training_need_request']['options']=='Training Need Request'

def test_learning_service_is_idempotent_and_standard_first():
    source=(ROOT/'qorg/qorg/employee_lifecycle/learning.py').read_text()
    for token in ('frappe.new_doc("Training Program")','frappe.new_doc("Training Event")','resolve_participants','already_converted','qorg_training_need_request'):
        assert token in source
    assert 'frappe.new_doc("Appraisal")' not in source
    assert 'frappe.new_doc("Employee Skill Map")' not in source

def test_permissions_and_hooks_are_registered():
    hooks=(ROOT/'qorg/hooks.py').read_text();ast.parse(hooks)
    for token in ('provision_learning_planning','training_need_query','development_action_query','training_need_request.js','development_action.js'):
        assert token in hooks
    permissions=(ROOT/'qorg/qorg/employee_lifecycle/learning_permissions.py').read_text()
    assert 'requested_by' in permissions and 'responsible_person' in permissions

def test_no_full_standard_field_order_override():
    provisioning=(ROOT/'qorg/qorg/employee_lifecycle/learning_provisioning.py').read_text()
    assert 'Property Setter' not in provisioning
    assert 'field_order' not in provisioning
