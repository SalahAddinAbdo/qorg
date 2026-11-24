import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
def test_audit_is_standard_first_and_read_only():
 source=(ROOT/'qorg/qorg/employee_lifecycle/learning_performance_audit.py').read_text();tree=ast.parse(source)
 for token in ('Training Event','Appraisal','Employee Skill Map','Training Need Request','Evaluation Assignment'):assert token in source
 for forbidden in ('.insert(','.save(','create_custom_fields','make_property_setter'):assert forbidden not in source
 assert {'run_audit','_inspect_doctype','_detect_conflicts','_recommendations'}<={n.name for n in tree.body if isinstance(n,ast.FunctionDef)}
def test_architecture_rules_are_explicit():
 text=(ROOT/'LEARNING_PERFORMANCE_PHASE_7_6A.md').read_text();assert 'Never replace the complete field order' in text;assert 'Python domain services own validation' in text
