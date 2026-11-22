import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]


def test_movement_hooks_and_provisioner_registered():
    source=(ROOT/'qorg/hooks.py').read_text()
    for token in ('Employee Promotion','Employee Transfer','validate_employee_movement','validate_salary_assignment','validate_funding_plan_movement','validate_contract_amendment_movement','provision_employee_movements'):
        assert token in source
    ast.parse(source)


def test_movement_engine_has_conflict_and_cancel_guards():
    source=(ROOT/'qorg/qorg/employee_lifecycle/movements.py').read_text()
    for token in ('_prevent_same_day_conflict','before_cancel_employee_movement','later movement','_validate_service_period','employee_movement_timeline'):
        assert token in source


def test_movement_custom_fields_cover_impacts_and_audit():
    source=(ROOT/'qorg/qorg/employee_lifecycle/movement_provisioning.py').read_text()
    for token in ('qorg_payroll_impact','qorg_funding_impact','qorg_contract_impact','qorg_previous_values','qorg_new_values'):
        assert token in source
