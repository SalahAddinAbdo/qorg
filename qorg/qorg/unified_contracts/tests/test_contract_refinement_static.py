import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]


def load_json(rel):
    return json.loads((ROOT / rel).read_text())


def test_contract_type_has_two_column_sections_and_policy_table():
    data = load_json('qorg/qorg/doctype/qorg_contract_type/qorg_contract_type.json')
    fields = {f['fieldname']: f for f in data['fields']}
    for name in ('identity_column','party_column','template_column','financial_column','operations_column','hr_column','lifecycle_column'):
        assert fields[name]['fieldtype'] == 'Column Break'
    assert fields['allowed_parties']['options'] == 'QOrg Contract Allowed Party'
    assert fields['party_model']['reqd'] == 1


def test_child_tables_exist_and_dynamic_link_is_valid():
    allowed = load_json('qorg/qorg/doctype/qorg_contract_allowed_party/qorg_contract_allowed_party.json')
    parties = load_json('qorg/qorg/doctype/qorg_contract_party/qorg_contract_party.json')
    assert allowed['istable'] == 1 and parties['istable'] == 1
    pfields = {f['fieldname']: f for f in parties['fields']}
    assert pfields['party']['fieldtype'] == 'Dynamic Link'
    assert pfields['party']['options'] == 'party_doctype'


def test_template_and_contract_refinement_fields_are_unique():
    module = ast.parse((ROOT / 'qorg/qorg/unified_contracts/refinement.py').read_text())
    names = {}
    for node in module.body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id.endswith('_FIELDS'):
            rows = ast.literal_eval(node.value)
            fieldnames = [r['fieldname'] for r in rows]
            assert len(fieldnames) == len(set(fieldnames))
            names[node.targets[0].id] = set(fieldnames)
    assert {'qorg_milestones','qorg_deliverables','qorg_guarantees','qorg_required_documents'} <= names['TEMPLATE_REFINEMENT_FIELDS']
    assert 'qorg_contract_parties' in names['CONTRACT_REFINEMENT_FIELDS']
