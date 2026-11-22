import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]


def test_source_of_truth_has_required_owners_and_change_paths():
    tree = ast.parse((ROOT / 'qorg/qorg/employee_lifecycle/source_of_truth.py').read_text())
    policy = None
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name) and node.targets[0].id == 'FIELD_POLICY':
            policy = ast.literal_eval(node.value)
    assert policy
    for key in ('company','designation','contract_period','salary_structure','funding_allocation','payroll_effective_date','leave_policy','shift'):
        assert policy[key]['owner'] and policy[key]['change_via'] and policy[key]['initial_precedence']


def test_readiness_engine_has_independent_services_and_no_overwrite():
    source = (ROOT / 'qorg/qorg/employee_lifecycle/activation.py').read_text()
    for service in ('employment','payroll','attendance','leave'):
        assert f'"{service}"' in source
    assert 'and not employee.get(fieldname)' in source
    assert 'Salary Structure Assignment' in source
    assert 'Leave Policy Assignment' in source
    assert 'Shift Assignment' in source
    assert 'Accounting Dimension' in source


def test_template_activation_fields_and_employee_readiness_fields_are_provisioned():
    source = (ROOT / 'qorg/qorg/employee_lifecycle/provisioning.py').read_text()
    for fieldname in ('qorg_holiday_list_required','qorg_shift_assignment_required','qorg_leave_policy_required','qorg_service_blockers','qorg_service_readiness_json'):
        assert fieldname in source


def test_employee_client_and_api_endpoints_exist():
    js = (ROOT / 'qorg/public/js/employee_lifecycle.js').read_text()
    api = (ROOT / 'qorg/qorg/employee_lifecycle/api.py').read_text()
    assert 'evaluate_readiness' in js and 'activate_services' in js
    assert 'def evaluate_readiness' in api and 'def activate_services' in api and 'def source_of_truth_policy' in api
