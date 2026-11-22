import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]


def test_recruitment_events_have_unique_entrypoints():
    tree = ast.parse((ROOT / 'qorg/qorg/recruitment_extensions/events.py').read_text())
    names = [node.name for node in tree.body if isinstance(node, ast.FunctionDef)]
    assert len(names) == len(set(names))


def test_work_commencement_can_prepare_employee_before_submit():
    data = json.loads((ROOT / 'qorg/qorg/doctype/work_commencement_notice/work_commencement_notice.json').read_text())
    fields = {row['fieldname']: row for row in data['fields']}
    assert not fields['employee'].get('reqd')
    assert fields['employment_contract']['options'] == 'Contract'
    assert fields['onboarding']['options'] == 'Employee Onboarding'


def test_lifecycle_service_is_idempotency_oriented():
    source = (ROOT / 'qorg/qorg/employee_lifecycle/service.py').read_text()
    for token in ('create_or_link_employee_from_commencement', 'create_or_link_employment_contract', 'create_or_link_onboarding', 'Multiple Employee records match'):
        assert token in source
    tree = ast.parse(source)
    functions = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
    assert {'prepare_commencement','finalize_commencement','_unique_existing_employee'} <= functions


def test_employee_lifecycle_provisioner_is_registered():
    source = (ROOT / 'qorg/hooks.py').read_text()
    assert "qorg.qorg.employee_lifecycle.provisioning.provision_employee_lifecycle" in source
    ast.parse(source)
