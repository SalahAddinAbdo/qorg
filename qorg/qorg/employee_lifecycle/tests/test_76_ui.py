import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
def load(slug):return json.loads((ROOT/f'qorg/qorg/doctype/{slug}/{slug}.json').read_text())
def field(slug,name):return next(x for x in load(slug)['fields'] if x['fieldname']==name)
def test_rich_text_and_tables_are_full_width_sections():
 for slug,name in [('training_need_request','justification'),('training_need_request','training_objectives'),('training_need_request','expected_outcomes'),('training_follow_up','follow_up_comments'),('evaluation_type','instructions')]:
  d=load(slug);i=next(i for i,x in enumerate(d['fields']) if x['fieldname']==name)
  assert any(x['fieldtype']=='Section Break' for x in d['fields'][:i])
  section=max(i for i,x in enumerate(d['fields'][:i]) if x['fieldtype']=='Section Break')
  assert not any(x['fieldtype']=='Column Break' for x in d['fields'][section:i])
 for slug,name in [('training_need_request','participants'),('evaluation_type','sources'),('rating_scale','bands')]:
  d=load(slug);i=next(i for i,x in enumerate(d['fields']) if x['fieldname']==name)
  section=max(i for i,x in enumerate(d['fields'][:i]) if x['fieldtype']=='Section Break')
  assert not any(x['fieldtype']=='Column Break' for x in d['fields'][section:i])
def test_critical_dependencies_are_explicit():
 assert field('training_need_request','requested_for_employee')['mandatory_depends_on']
 assert field('training_need_request','designation')['mandatory_depends_on']
 assert field('training_need_request','project')['mandatory_depends_on']
 assert field('training_need_request','source_document')['mandatory_depends_on']
 assert field('development_action','training_need_request')['mandatory_depends_on']
 assert field('training_follow_up','recommended_action')['mandatory_depends_on']
 assert field('evaluation_assignment','related_department')['depends_on']
def test_link_filters_cover_operational_fields():
 files={p.name:p.read_text() for p in (ROOT/'qorg/public/js').glob('*.js')}
 checks={
  'training_need_request.js':['branch','department','project','cost_center','funding_agreement','budget_line','requested_for_employee','source_document'],
  'development_action.js':['employee','responsible_person','source_document','training_need_request','completion_document'],
  'training_assessment.js':['training_event','employee','assessor','evidence'],
  'training_follow_up.js':['training_event','training_result','responsible_user','evidence_document','recommended_action'],
  'evaluation_assignment.js':['reviewer','appraisal_cycle','appraisal','evaluation_type','feedback'],
 }
 for filename,fields in checks.items():
  for name in fields:assert f"set_query('{name}'" in files[filename],f'{filename}:{name}'
def test_reviewer_query_excludes_subject_and_requires_user():
 source=(ROOT/'qorg/qorg/employee_lifecycle/perf_query.py').read_text()
 assert 'employee.name != employee_name' in source
 assert 'employee.user_id.isnotnull()' in source
