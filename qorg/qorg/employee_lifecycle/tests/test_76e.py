import ast,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
def load(slug):return json.loads((ROOT/f'qorg/qorg/doctype/{slug}/{slug}.json').read_text())
def test_result_and_calculation_log_are_protected_child_tables():
 for slug,name in [('evaluation_result','Evaluation Result'),('calculation_log','Calculation Log')]:
  d=load(slug);assert d['name']==name and d['istable']==1 and d['editable_grid']==0
  assert all(f.get('read_only') for f in d['fields'] if f['fieldtype'] not in {'Section Break','Column Break'})
def test_calculation_policies_and_stage_machine_exist():
 source=(ROOT/'qorg/qorg/employee_lifecycle/performance.py').read_text()
 for token in ('Strict Completion','Completed Weight','Reallocate Weight','STAGE_TRANSITIONS','recalculate_appraisal','transition_appraisal','protect_appraisal'):
  assert token in source
def test_finalization_and_reopen_guards_exist():
 source=(ROOT/'qorg/qorg/employee_lifecycle/performance.py').read_text()
 assert 'configured completion policy' in source
 assert 'A Development Action is required before finalizing this outcome' in source
 assert 'Finalized Appraisal content and results are protected' in source
def test_standard_appraisal_is_extended_not_replaced():
 setup=(ROOT/'qorg/qorg/employee_lifecycle/perf_setup.py').read_text()
 for token in ('qorg_stage','qorg_source_results','Evaluation Result','qorg_calc_log'):
  assert token in setup
 assert not (ROOT/'qorg/qorg/doctype/appraisal').exists()
def test_client_actions_and_hooks_registered():
 js=(ROOT/'qorg/public/js/appraisal_ext.js').read_text()
 for token in ('Recalculate','Finalized','Reopened','Cancelled','perf_api.transition'):assert token in js
 hooks=(ROOT/'qorg/hooks.py').read_text();ast.parse(hooks);assert 'performance.protect_appraisal' in hooks
def test_layout_uses_dedicated_tab_sections_and_columns():
 setup=(ROOT/'qorg/qorg/employee_lifecycle/perf_setup.py').read_text()
 assert 'Tab Break' in setup and 'Section Break' in setup and 'Column Break' in setup
