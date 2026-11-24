import ast,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
def load(slug):return json.loads((ROOT/f'qorg/qorg/doctype/{slug}/{slug}.json').read_text())
def test_compact_policy_models_exist():
 expected={'Rating Scale','Rating Band','Evaluation Type','Evaluation Source','Evaluation Assignment'}
 actual={load(x)['name'] for x in ('rating_scale','rating_band','evaluation_type','evaluation_source','evaluation_assignment')}
 assert actual==expected
def test_sources_and_rating_bands_are_child_tables():
 assert load('evaluation_source')['istable']==1
 assert load('rating_band')['istable']==1
 assert {f['fieldname']:f for f in load('evaluation_type')['fields']}['sources']['options']=='Evaluation Source'
 assert {f['fieldname']:f for f in load('rating_scale')['fields']}['bands']['options']=='Rating Band'
def test_policy_rules_and_assignment_guards_exist():
 source=(ROOT/'qorg/qorg/employee_lifecycle/performance.py').read_text()
 for token in ('Included Evaluation Source weights must total 100','Rating bands must cover the full 0 to 100 range','generate_assignments','replace_assignment','decline_assignment','validate_feedback','qorg_policy_snapshot'):
  assert token in source
 assert 'frappe.new_doc("Appraisal")' not in source
def test_standard_models_are_extended_not_replaced():
 setup=(ROOT/'qorg/qorg/employee_lifecycle/perf_setup.py').read_text()
 for dt in ('Appraisal Cycle','Appraisal','Employee Performance Feedback'):assert f'"{dt}"' in setup
 assert 'field_order' not in setup and 'Property Setter' not in setup
def test_hooks_permissions_and_js_registered():
 hooks=(ROOT/'qorg/hooks.py').read_text();ast.parse(hooks)
 for token in ('setup_performance_policy','assignment_query','validate_appraisal_cycle','validate_feedback','evaluation_type.js','evaluation_assignment.js','appraisal_ext.js'):
  assert token in hooks
def test_layout_uses_sections_and_columns():
 for slug in ('rating_scale','evaluation_type','evaluation_assignment'):
  types=[f['fieldtype'] for f in load(slug)['fields']]
  assert 'Section Break' in types and 'Column Break' in types
